import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.models.billing import Payment, Subscription
from backend.app.models.user import User
from backend.app.schemas.billing import (
    CancelSubscriptionResponse,
    CheckoutRequest,
    CheckoutResponse,
    PlanCatalogResponse,
    SubscriptionResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)
from backend.app.services.razorpay_service import (
    PLAN_CATALOG,
    RazorpayService,
    utcnow,
)

logger = logging.getLogger("contently.routes.billing")

router = APIRouter(prefix="/api/billing", tags=["Billing & Subscriptions"])


@router.get("/plans", response_model=PlanCatalogResponse, status_code=status.HTTP_200_OK)
def list_subscription_plans():
    """Retrieve available Contently subscription plans from authoritative backend catalog."""
    plans = RazorpayService.get_plan_catalog()
    return {
        "plans": plans,
        "active_currency": settings.RAZORPAY_CURRENCY or "INR",
    }


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_200_OK)
def create_checkout_session(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initialize a secure Razorpay checkout session for the authenticated user.
    Price and amount are strictly determined on the backend and cannot be tampered with.
    """
    session_data = RazorpayService.create_checkout_session(
        user=current_user,
        plan_code=req.plan_code,
        requested_currency=req.currency,
    )
    return session_data


@router.get("/subscription", response_model=SubscriptionResponse, status_code=status.HTTP_200_OK)
def get_user_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Read the signed-in user's active subscription status, plan tier, and payment history."""
    return RazorpayService.get_user_subscription_status(db, current_user)


@router.post("/verify-payment", response_model=VerifyPaymentResponse, status_code=status.HTTP_200_OK)
def verify_checkout_payment(
    req: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verify payment signature from Razorpay Checkout client callback.
    Guarantees the payment is authentic before acknowledging client.
    Authoritative state is synchronized via webhook event.
    """
    is_valid = RazorpayService.verify_checkout_signature(
        payment_id=req.razorpay_payment_id,
        signature=req.razorpay_signature,
        subscription_id=req.razorpay_subscription_id,
        order_id=req.razorpay_order_id,
    )

    if not is_valid:
        logger.warning(
            "Payment signature verification failed for user %s (pay_id=%s)",
            current_user.id,
            req.razorpay_payment_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment signature verification failed. Please contact support.",
        )

    # Record verified payment in database
    existing_payment = (
        db.query(Payment)
        .filter(Payment.razorpay_payment_id == req.razorpay_payment_id)
        .first()
    )
    plan_info = PLAN_CATALOG.get(req.plan_code or "pro_monthly", PLAN_CATALOG["pro_monthly"])
    amount, currency = RazorpayService.determine_amount_and_currency(plan_info)

    if not existing_payment:
        sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
        payment_record = Payment(
            user_id=current_user.id,
            subscription_id=sub.id if sub else None,
            razorpay_payment_id=req.razorpay_payment_id,
            razorpay_order_id=req.razorpay_order_id,
            razorpay_signature=req.razorpay_signature,
            amount=amount,
            currency=currency,
            status="authorized",
        )
        db.add(payment_record)

        # Update local subscription to active/authenticated
        if not sub:
            sub = Subscription(
                user_id=current_user.id,
                plan_code=req.plan_code or "pro_monthly",
                plan_name=plan_info["name"],
                status="active",
                razorpay_subscription_id=req.razorpay_subscription_id,
                current_start=utcnow(),
                current_end=utcnow() + (
                    __import__("datetime").timedelta(days=365 if plan_info["interval"] == "yearly" else 30)
                ),
            )
            db.add(sub)
        else:
            sub.status = "active"
            sub.plan_code = req.plan_code or "pro_monthly"
            sub.plan_name = plan_info["name"]
            if req.razorpay_subscription_id:
                sub.razorpay_subscription_id = req.razorpay_subscription_id

        current_user.role = "Pro Creator"
        db.commit()

    return {
        "success": True,
        "status": "verified",
        "message": "Payment signature verified successfully. Subscription is active.",
        "payment_id": req.razorpay_payment_id,
        "subscription_status": "active",
    }


@router.post("/cancel", response_model=CancelSubscriptionResponse, status_code=status.HTTP_200_OK)
def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Request cancellation of the current active subscription."""
    return RazorpayService.cancel_user_subscription(db, current_user)


@router.post("/free-tier", status_code=status.HTTP_200_OK)
def activate_free_tier(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Switch user to the Free Starter Freemium Tier with 10,000 monthly tokens at ₹0."""
    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    if sub:
        sub.status = "free"
        sub.plan_code = "free"
        sub.plan_name = "Free Starter Tier"
        sub.cancelled_at = utcnow()
    current_user.role = "Free Creator"
    db.commit()
    return {
        "success": True,
        "status": "free",
        "plan_code": "free",
        "message": "Switched to Free Starter plan successfully! 10,000 monthly inference tokens active at ₹0.",
    }


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: str = Header(None, alias="X-Razorpay-Signature"),
):
    """
    Authoritative Razorpay Webhook receiver.
    Verifies HMAC SHA-256 signature using the raw request body.
    Ensures idempotent processing against duplicate event retries.
    """
    raw_body = await request.body()

    if not x_razorpay_signature:
        logger.warning("Rejected webhook: missing X-Razorpay-Signature header.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Razorpay-Signature header.",
        )

    # 1. Authoritative Webhook Signature Verification
    if not RazorpayService.verify_webhook_signature(raw_body, x_razorpay_signature):
        logger.warning("Rejected webhook: invalid signature header.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature.",
        )

    # 2. Parse payload safely
    try:
        raw_body_str = raw_body.decode("utf-8")
        payload = json.loads(raw_body_str)
    except Exception as e:
        logger.error("Failed to parse webhook JSON body: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed JSON payload.",
        )

    # 3. Idempotent event processing & database update
    result = RazorpayService.process_webhook_event(db, payload, raw_body_str)
    logger.info("Processed webhook event: %s", result)

    return {
        "success": True,
        "event_id": result.get("event_id"),
        "event_type": result.get("event_type"),
        "status": result.get("status"),
    }
