import hashlib
import hmac
import logging
import time
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.billing import Payment, Subscription, WebhookEvent
from backend.app.models.user import User

logger = logging.getLogger("contently.razorpay")


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def to_naive_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


PLAN_CATALOG: dict[str, dict[str, Any]] = {
    "free": {
        "id": "free",
        "name": "Free Starter Tier",
        "tier_name": "Free Starter",
        "interval": "lifetime",
        "price_usd": 0.0,
        "amount_usd_cents": 0,
        "price_inr": 0.0,
        "amount_inr_paise": 0,
        "description": "Free forever freemium tier - explore AI content creation with no credit card required",
        "features": [
            "10,000 monthly AI inference tokens",
            "1 Custom Brand Kit voice slot",
            "Standard Social & Blog AI templates",
            "Full Content Editor & local drafts",
            "Community knowledge base access",
        ],
    },
    "pro_monthly": {
        "id": "pro_monthly",
        "name": "Pro Creator Tier (Monthly)",
        "tier_name": "Pro Creator Tier",
        "interval": "monthly",
        "price_usd": 6.0,
        "amount_usd_cents": 600,
        "price_inr": 499.0,
        "amount_inr_paise": 49900,
        "description": "Reasonable Pro plan for creators - full generative inference and multi-channel pipeline",
        "features": [
            "Unlimited AI content generation",
            "500,000 monthly inference tokens",
            "5 Brand Kit custom voice profiles",
            "Multi-channel automated publishing",
            "SEO Assistant & Long-form Repurposing",
            "Instant UPI Autopay & Card checkout",
        ],
    },
    "pro_yearly": {
        "id": "pro_yearly",
        "name": "Pro Creator Tier (Yearly)",
        "tier_name": "Pro Creator Tier",
        "interval": "yearly",
        "price_usd": 58.0,
        "amount_usd_cents": 5800,
        "price_inr": 4790.0,
        "amount_inr_paise": 479000,
        "description": "Pro Creator Tier (Annual) - Save 20% on year-round access (₹399/mo equivalent)",
        "features": [
            "All Pro Creator Tier monthly features",
            "20% annual discount applied (₹399/mo equivalent · 2 months free)",
            "Priority AI inference processing",
            "Dedicated creator onboarding support",
        ],
    },
    "agency_monthly": {
        "id": "agency_monthly",
        "name": "Agency & Studio Team",
        "tier_name": "Agency Tier",
        "interval": "monthly",
        "price_usd": 18.0,
        "amount_usd_cents": 1800,
        "price_inr": 1499.0,
        "amount_inr_paise": 149900,
        "description": "For high-volume content studios, marketing agencies, and creator teams",
        "features": [
            "2,500,000 monthly inference tokens",
            "Unlimited Brand Kit voice profiles",
            "Up to 5 collaborative team seats",
            "Priority autonomous agent queue",
            "Dedicated WhatsApp & VIP support",
        ],
    },
}


class RazorpayService:
    @classmethod
    def get_client(cls):
        """Instantiate official Razorpay client with credentials from environment."""
        key_id = settings.RAZORPAY_KEY_ID
        key_secret = settings.RAZORPAY_KEY_SECRET

        if not key_id or not key_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Razorpay payments are not yet configured on this server. "
                    "Please set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in backend/.env."
                ),
            )

        try:
            import razorpay
            return razorpay.Client(auth=(key_id, key_secret))
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Razorpay python SDK is not installed on server.",
            )

    @classmethod
    def get_plan_catalog(cls) -> list[dict[str, Any]]:
        """Return canonical plan catalog with pricing and feature inclusions."""
        return list(PLAN_CATALOG.values())

    @classmethod
    def get_plan(cls, plan_code: str) -> dict[str, Any]:
        """Fetch and validate a plan code strictly on the server."""
        if plan_code not in PLAN_CATALOG:
            valid_codes = ", ".join(PLAN_CATALOG.keys())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid plan code '{plan_code}'. Must be one of: {valid_codes}.",
            )
        return PLAN_CATALOG[plan_code]

    @classmethod
    def determine_amount_and_currency(
        cls, plan: dict[str, Any], requested_currency: str | None = None
    ) -> tuple[int, str]:
        """Determine charge amount and currency based on backend settings and plan catalog."""
        currency = (requested_currency or settings.RAZORPAY_CURRENCY or "INR").upper()
        if currency == "USD":
            amount = plan["amount_usd_cents"]
        else:
            currency = "INR"
            amount = plan["amount_inr_paise"]
        return amount, currency

    @classmethod
    def create_checkout_session(
        cls,
        user: User,
        plan_code: str,
        requested_currency: str | None = None,
    ) -> dict[str, Any]:
        """Create a Razorpay subscription or order session for authenticated user."""
        plan = cls.get_plan(plan_code)
        amount, currency = cls.determine_amount_and_currency(plan, requested_currency)

        # Free Freemium Tier needs no payment gateway order
        if plan_code == "free" or amount == 0:
            return {
                "key_id": settings.RAZORPAY_KEY_ID or "free_freemium",
                "subscription_id": None,
                "order_id": None,
                "amount": 0,
                "currency": "INR",
                "plan_code": "free",
                "plan_name": plan["name"],
                "tier_name": plan["tier_name"],
                "billing_interval": plan["interval"],
                "prefill": {
                    "name": user.full_name or "Contently Creator",
                    "email": user.email,
                },
                "notes": {
                    "user_id": str(user.id),
                    "plan_code": "free",
                },
                "checkout_type": "free",
            }

        client = cls.get_client()

        # Check for configured Razorpay recurring Plan ID
        razorpay_plan_id = None
        if plan_code == "pro_monthly" and settings.RAZORPAY_PLAN_PRO_MONTHLY:
            razorpay_plan_id = settings.RAZORPAY_PLAN_PRO_MONTHLY
        elif plan_code == "pro_yearly" and settings.RAZORPAY_PLAN_PRO_YEARLY:
            razorpay_plan_id = settings.RAZORPAY_PLAN_PRO_YEARLY

        subscription_id = None
        order_id = None
        checkout_type = "order"

        # If a Razorpay plan ID is configured, create Razorpay Subscription
        if razorpay_plan_id:
            try:
                sub_payload = {
                    "plan_id": razorpay_plan_id,
                    "total_count": 12 if plan["interval"] == "monthly" else 5,
                    "quantity": 1,
                    "customer_notify": 1,
                    "notes": {
                        "user_id": str(user.id),
                        "user_email": user.email,
                        "plan_code": plan_code,
                    },
                }
                sub_res = client.subscription.create(sub_payload)
                subscription_id = sub_res.get("id")
                checkout_type = "subscription"
                logger.info(
                    "Created Razorpay subscription '%s' for user %s (plan=%s)",
                    subscription_id,
                    user.id,
                    plan_code,
                )
            except Exception as e:
                logger.warning(
                    "Razorpay subscription creation failed, falling back to order creation: %s",
                    str(e),
                )
                # Fall through to order creation if recurring subscription creation fails

        # If no subscription created, create a standard Razorpay Order
        if not subscription_id:
            receipt = f"rcpt_u{user.id}_{int(time.time())}"
            order_payload = {
                "amount": amount,
                "currency": currency,
                "receipt": receipt,
                "notes": {
                    "user_id": str(user.id),
                    "user_email": user.email,
                    "plan_code": plan_code,
                    "plan_name": plan["name"],
                },
            }
            try:
                order_res = client.order.create(order_payload)
                order_id = order_res.get("id")
                checkout_type = "order"
                logger.info(
                    "Created Razorpay order '%s' for user %s (amount=%s %s)",
                    order_id,
                    user.id,
                    amount,
                    currency,
                )
            except Exception as e:
                logger.error("Razorpay order creation failed: %s", str(e), exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Unable to initialize Razorpay checkout: {e!s}",
                )

        return {
            "key_id": settings.RAZORPAY_KEY_ID,
            "subscription_id": subscription_id,
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "plan_code": plan_code,
            "plan_name": plan["name"],
            "tier_name": plan["tier_name"],
            "billing_interval": plan["interval"],
            "prefill": {
                "name": user.full_name or "Contently Creator",
                "email": user.email,
            },
            "notes": {
                "user_id": str(user.id),
                "plan_code": plan_code,
            },
            "checkout_type": checkout_type,
        }

    @classmethod
    def verify_checkout_signature(
        cls,
        payment_id: str,
        signature: str,
        subscription_id: str | None = None,
        order_id: str | None = None,
    ) -> bool:
        """Verify Razorpay payment signature according to official algorithm."""
        key_secret = settings.RAZORPAY_KEY_SECRET
        if not key_secret:
            logger.error("Cannot verify signature: RAZORPAY_KEY_SECRET is not set.")
            return False

        try:
            if subscription_id:
                # Subscription verification string: payment_id + "|" + subscription_id
                data = f"{payment_id}|{subscription_id}"
            elif order_id:
                # Order verification string: order_id + "|" + payment_id
                data = f"{order_id}|{payment_id}"
            else:
                return False

            expected = hmac.new(
                key_secret.encode("utf-8"), data.encode("utf-8"), hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(expected, signature)
        except Exception as e:
            logger.error("Error during checkout signature verification: %s", str(e))
            return False

    @classmethod
    def verify_webhook_signature(cls, raw_body: bytes, signature: str) -> bool:
        """Verify Razorpay Webhook signature securely using raw request bytes."""
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        if not webhook_secret:
            logger.error("Cannot verify webhook signature: RAZORPAY_WEBHOOK_SECRET is not set.")
            return False

        try:
            expected = hmac.new(
                webhook_secret.encode("utf-8"), raw_body, hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception as e:
            logger.error("Error verifying webhook signature: %s", str(e))
            return False

    @classmethod
    def process_webhook_event(
        cls, db: Session, event_payload: dict[str, Any], raw_body_str: str
    ) -> dict[str, Any]:
        """Idempotently process incoming verified Razorpay webhook event."""
        # 1. Extract Event ID & Type
        event_id = (
            event_payload.get("event_id")
            or event_payload.get("id")
            or (
                event_payload.get("payload", {})
                .get("payment", {})
                .get("entity", {})
                .get("id")
            )
        )
        event_type = event_payload.get("event", "unknown")

        if not event_id:
            # Fallback deterministic event id based on hash of raw body
            event_id = f"evt_hash_{hashlib.sha256(raw_body_str.encode()).hexdigest()[:24]}"

        # 2. Check Idempotency Ledger
        existing_event = (
            db.query(WebhookEvent).filter(WebhookEvent.event_id == event_id).first()
        )
        if existing_event:
            logger.info("Webhook event '%s' (%s) was already processed. Skipping.", event_id, event_type)
            return {
                "event_id": event_id,
                "event_type": event_type,
                "status": "already_processed",
                "idempotent": True,
            }

        # 3. Process according to Razorpay Webhook event type
        payload_data = event_payload.get("payload", {})
        sub_entity = payload_data.get("subscription", {}).get("entity", {})
        payment_entity = payload_data.get("payment", {}).get("entity", {})
        order_entity = payload_data.get("order", {}).get("entity", {})

        # Extract user identification from notes
        notes = (
            sub_entity.get("notes")
            or payment_entity.get("notes")
            or order_entity.get("notes")
            or {}
        )
        user_id_str = notes.get("user_id")
        user_email = notes.get("user_email")
        plan_code = notes.get("plan_code", "pro_monthly")

        user = None
        if user_id_str and str(user_id_str).isdigit():
            user = db.query(User).filter(User.id == int(user_id_str)).first()
        elif user_email:
            user = db.query(User).filter(User.email == user_email).first()

        # If user not found via notes, try matching from razorpay_subscription_id
        razorpay_sub_id = sub_entity.get("id") or payment_entity.get("subscription_id")
        existing_sub = None
        if razorpay_sub_id:
            existing_sub = (
                db.query(Subscription)
                .filter(Subscription.razorpay_subscription_id == razorpay_sub_id)
                .first()
            )
            if existing_sub and not user:
                user = db.query(User).filter(User.id == existing_sub.user_id).first()

        now = utcnow()
        plan_info = PLAN_CATALOG.get(plan_code, PLAN_CATALOG["pro_monthly"])
        duration_days = 365 if plan_info["interval"] == "yearly" else 30

        # Handle Subscriptions & Payments based on authoritative webhook event
        if event_type in (
            "subscription.authenticated",
            "subscription.activated",
            "subscription.charged",
            "order.paid",
            "payment.captured",
        ):
            if user:
                sub = existing_sub or db.query(Subscription).filter(Subscription.user_id == user.id).first()
                if not sub:
                    sub = Subscription(
                        user_id=user.id,
                        plan_code=plan_code,
                        plan_name=plan_info["name"],
                        status="active",
                        razorpay_subscription_id=razorpay_sub_id,
                        razorpay_plan_id=sub_entity.get("plan_id"),
                        current_start=now,
                        current_end=now + timedelta(days=duration_days),
                        cancel_at_period_end=False,
                    )
                    db.add(sub)
                    db.flush()
                else:
                    sub.status = "active"
                    sub.plan_code = plan_code
                    sub.plan_name = plan_info["name"]
                    if razorpay_sub_id:
                        sub.razorpay_subscription_id = razorpay_sub_id
                    sub.current_start = now
                    sub.current_end = now + timedelta(days=duration_days)
                    sub.cancel_at_period_end = False

                # Ensure user role reflects active tier
                user.role = "Pro Creator"

                # Record Payment if payment entity is present
                pay_id = payment_entity.get("id")
                if pay_id:
                    existing_payment = (
                        db.query(Payment)
                        .filter(Payment.razorpay_payment_id == pay_id)
                        .first()
                    )
                    if not existing_payment:
                        pay_record = Payment(
                            user_id=user.id,
                            subscription_id=sub.id,
                            razorpay_payment_id=pay_id,
                            razorpay_order_id=payment_entity.get("order_id"),
                            amount=payment_entity.get("amount", plan_info["amount_inr_paise"]),
                            currency=payment_entity.get("currency", settings.RAZORPAY_CURRENCY or "INR"),
                            status=payment_entity.get("status", "captured"),
                            method=payment_entity.get("method"),
                        )
                        db.add(pay_record)

                logger.info(
                    "Authoritative activation for user %s via webhook event '%s'",
                    user.id,
                    event_type,
                )

        elif event_type in ("subscription.pending",):
            if existing_sub:
                existing_sub.status = "pending"
            elif user:
                sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
                if sub:
                    sub.status = "pending"

        elif event_type in ("subscription.halted", "payment.failed"):
            if existing_sub:
                existing_sub.status = "past_due"
            elif user:
                sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
                if sub:
                    sub.status = "past_due"

            # Record failed payment record if payment entity present
            if user and payment_entity.get("id"):
                pay_id = payment_entity.get("id")
                existing_payment = (
                    db.query(Payment).filter(Payment.razorpay_payment_id == pay_id).first()
                )
                if not existing_payment:
                    failed_pay = Payment(
                        user_id=user.id,
                        subscription_id=existing_sub.id if existing_sub else None,
                        razorpay_payment_id=pay_id,
                        razorpay_order_id=payment_entity.get("order_id"),
                        amount=payment_entity.get("amount", 0),
                        currency=payment_entity.get("currency", settings.RAZORPAY_CURRENCY or "INR"),
                        status="failed",
                        method=payment_entity.get("method"),
                        error_code=payment_entity.get("error_code"),
                        error_description=payment_entity.get("error_description"),
                    )
                    db.add(failed_pay)

        elif event_type in ("subscription.cancelled",):
            if existing_sub:
                existing_sub.status = "cancelled"
                existing_sub.cancelled_at = now
            elif user:
                sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
                if sub:
                    sub.status = "cancelled"
                    sub.cancelled_at = now

        # 4. Save Event to WebhookEvent table for Idempotency
        webhook_log = WebhookEvent(
            event_id=event_id,
            event_type=event_type,
            status="processed",
            payload=raw_body_str,
            processed_at=now,
        )
        db.add(webhook_log)
        db.commit()

        return {
            "event_id": event_id,
            "event_type": event_type,
            "status": "processed",
            "idempotent": False,
        }

    @classmethod
    def cancel_user_subscription(cls, db: Session, user: User) -> dict[str, Any]:
        """Request cancellation of the signed-in user's active subscription."""
        sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
        if not sub or sub.status not in ("active", "authenticated", "pending"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You do not currently have an active subscription to cancel.",
            )

        # If connected to a live Razorpay subscription, request cancellation on Razorpay API
        if sub.razorpay_subscription_id and settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
            try:
                client = cls.get_client()
                client.subscription.cancel(
                    sub.razorpay_subscription_id,
                    {"cancel_at_cycle_end": 1},
                )
                logger.info("Cancelled Razorpay subscription %s", sub.razorpay_subscription_id)
            except Exception as e:
                logger.warning(
                    "Razorpay subscription cancellation request error (will update local DB): %s",
                    str(e),
                )

        sub.cancel_at_period_end = True
        sub.cancelled_at = utcnow()
        sub.status = "cancelled"
        db.commit()
        db.refresh(sub)

        return {
            "success": True,
            "status": "cancelled",
            "message": "Your Pro Creator subscription has been cancelled. Access will remain active until current period end.",
        }

    @classmethod
    def get_user_subscription_status(cls, db: Session, user: User) -> dict[str, Any]:
        """Fetch current user's subscription, plan tier, and payment history."""
        sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
        payments = (
            db.query(Payment)
            .filter(Payment.user_id == user.id)
            .order_by(Payment.created_at.desc())
            .limit(10)
            .all()
        )

        is_active = False
        plan_code = "free"
        plan_name = "Free Creator"
        tier_name = "Free Creator"
        status_val = "free"

        if sub:
            status_val = sub.status
            plan_code = sub.plan_code
            plan_name = sub.plan_name
            tier_name = "Pro Creator Tier"
            if sub.status in ("active", "authenticated"):
                current_end_naive = to_naive_utc(sub.current_end)
                if not current_end_naive or current_end_naive >= utcnow():
                    is_active = True
        elif user.role == "Pro Creator":
            # Seeded demo state or default trial
            is_active = True
            plan_code = "pro_monthly"
            plan_name = "Pro Creator Tier (Monthly)"
            tier_name = "Pro Creator Tier"
            status_val = "active"

        return {
            "status": status_val,
            "is_active": is_active,
            "plan_code": plan_code,
            "plan_name": plan_name,
            "tier_name": tier_name,
            "current_start": sub.current_start if sub else None,
            "current_end": sub.current_end if sub else None,
            "cancel_at_period_end": sub.cancel_at_period_end if sub else False,
            "cancelled_at": sub.cancelled_at if sub else None,
            "recent_payments": payments,
        }
