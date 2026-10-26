import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

from backend.app.core.config import settings
from backend.app.models.billing import Payment, Subscription
from backend.app.models.user import User


def test_billing_plans_list(client):
    """Verify backend plans catalog returns correct plans, prices, and features."""
    resp = client.get("/api/billing/plans")
    assert resp.status_code == 200
    data = resp.json()
    assert "plans" in data
    assert data["active_currency"] == "INR"
    plan_codes = [p["id"] for p in data["plans"]]
    assert "free" in plan_codes
    assert "pro_monthly" in plan_codes
    assert "pro_yearly" in plan_codes
    assert "agency_monthly" in plan_codes

    free = next(p for p in data["plans"] if p["id"] == "free")
    assert free["price_inr"] == 0.0
    assert free["amount_inr_paise"] == 0

    monthly = next(p for p in data["plans"] if p["id"] == "pro_monthly")
    assert monthly["price_inr"] == 499.0
    assert monthly["amount_inr_paise"] == 49900
    assert monthly["price_usd"] == 6.0
    assert monthly["amount_usd_cents"] == 600
    assert monthly["interval"] == "monthly"

    yearly = next(p for p in data["plans"] if p["id"] == "pro_yearly")
    assert yearly["price_inr"] == 4790.0
    assert yearly["amount_inr_paise"] == 479000
    assert yearly["price_usd"] == 58.0
    assert yearly["amount_usd_cents"] == 5800
    assert yearly["interval"] == "yearly"


def test_checkout_unauthenticated(client):
    """Starting checkout without authentication is rejected."""
    resp = client.post("/api/billing/checkout", json={"plan_code": "pro_monthly"})
    assert resp.status_code == 401


def test_checkout_free_tier_requires_no_gateway(client, demo_auth_headers):
    """Free freemium tier does not require payment gateway credentials."""
    resp = client.post(
        "/api/billing/checkout",
        json={"plan_code": "free"},
        headers=demo_auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["amount"] == 0
    assert data["checkout_type"] == "free"
    assert data["plan_code"] == "free"


def test_activate_free_tier_endpoint(client, demo_auth_headers):
    """Authenticated user can switch to free freemium tier with 1 click."""
    resp = client.post("/api/billing/free-tier", headers=demo_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["status"] == "free"


def test_checkout_invalid_plan(client, demo_auth_headers):
    """Requesting checkout with an invalid plan code returns 400."""
    resp = client.post(
        "/api/billing/checkout",
        json={"plan_code": "non_existent_tier"},
        headers=demo_auth_headers,
    )
    assert resp.status_code == 400
    assert "Invalid plan code" in resp.json()["detail"]


def test_checkout_missing_credentials_returns_503(client, demo_auth_headers):
    """When Razorpay credentials are not configured, clear 503 is returned."""
    with patch.object(settings, "RAZORPAY_KEY_ID", ""), patch.object(
        settings, "RAZORPAY_KEY_SECRET", ""
    ):
        resp = client.post(
            "/api/billing/checkout",
            json={"plan_code": "pro_monthly"},
            headers=demo_auth_headers,
        )
        assert resp.status_code == 503
        assert "RAZORPAY_KEY_ID" in resp.json()["detail"]


def test_checkout_creation_order_flow(client, demo_auth_headers):
    """Checkout initializes Razorpay order session in INR and returns client parameters."""
    mock_order = {"id": "order_test_998877", "amount": 49900, "currency": "INR"}
    mock_client = MagicMock()
    mock_client.order.create.return_value = mock_order

    with patch.object(settings, "RAZORPAY_KEY_ID", "rzp_test_mock123"), \
         patch.object(settings, "RAZORPAY_KEY_SECRET", "mock_secret_abc"), \
         patch("backend.app.services.razorpay_service.RazorpayService.get_client", return_value=mock_client):

        resp = client.post(
            "/api/billing/checkout",
            json={"plan_code": "pro_monthly"},
            headers=demo_auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["key_id"] == "rzp_test_mock123"
        assert data["order_id"] == "order_test_998877"
        assert data["amount"] == 49900
        assert data["currency"] == "INR"
        assert data["plan_code"] == "pro_monthly"
        assert "prefill" in data
        assert data["prefill"]["email"] == settings.DEMO_USER_EMAIL


def test_verify_payment_invalid_signature(client, demo_auth_headers):
    """Tampered or fraudulent payment signatures are rejected."""
    with patch.object(settings, "RAZORPAY_KEY_SECRET", "secret_key_123"):
        resp = client.post(
            "/api/billing/verify-payment",
            json={
                "razorpay_payment_id": "pay_fake_111",
                "razorpay_order_id": "order_fake_222",
                "razorpay_signature": "invalid_signature_hash",
                "plan_code": "pro_monthly",
            },
            headers=demo_auth_headers,
        )
        assert resp.status_code == 400
        assert "verification failed" in resp.json()["detail"]


def test_verify_payment_valid_signature(client, demo_auth_headers):
    """Valid checkout signature authorizes payment and records in database."""
    secret = "test_key_secret_456"
    pay_id = "pay_valid_12345"
    order_id = "order_valid_67890"
    valid_sig = hmac.new(
        secret.encode(), f"{order_id}|{pay_id}".encode(), hashlib.sha256
    ).hexdigest()

    with patch.object(settings, "RAZORPAY_KEY_SECRET", secret):
        resp = client.post(
            "/api/billing/verify-payment",
            json={
                "razorpay_payment_id": pay_id,
                "razorpay_order_id": order_id,
                "razorpay_signature": valid_sig,
                "plan_code": "pro_monthly",
            },
            headers=demo_auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["status"] == "verified"


def test_webhook_missing_signature_rejected(client):
    """Webhooks without X-Razorpay-Signature header are rejected."""
    resp = client.post("/api/billing/webhook", json={"event": "subscription.charged"})
    assert resp.status_code == 400
    assert "Missing X-Razorpay-Signature" in resp.json()["detail"]


def test_webhook_invalid_signature_rejected(client):
    """Webhooks with mismatched HMAC signature are rejected."""
    with patch.object(settings, "RAZORPAY_WEBHOOK_SECRET", "correct_secret"):
        resp = client.post(
            "/api/billing/webhook",
            content=json.dumps({"event": "subscription.charged"}),
            headers={"X-Razorpay-Signature": "wrong_signature_here", "Content-Type": "application/json"},
        )
        assert resp.status_code == 400
        assert "Invalid webhook signature" in resp.json()["detail"]


def test_webhook_subscription_charged_activates_subscription(client, db_session):
    """Verified webhook updates user subscription to active and creates payment record."""
    user = db_session.query(User).filter(User.email == settings.DEMO_USER_EMAIL).first()
    webhook_secret = "webhook_secret_test_xyz"

    event_payload = {
        "event": "subscription.charged",
        "event_id": "evt_test_charge_1001",
        "payload": {
            "subscription": {
                "entity": {
                    "id": "sub_test_live_88",
                    "plan_id": "plan_test_pro",
                    "notes": {"user_id": str(user.id), "plan_code": "pro_monthly"},
                }
            },
            "payment": {
                "entity": {
                    "id": "pay_test_charge_2002",
                    "order_id": "order_test_sub_3003",
                    "amount": 4900,
                    "currency": "USD",
                    "status": "captured",
                    "method": "card",
                }
            },
        },
    }

    raw_body = json.dumps(event_payload).encode("utf-8")
    valid_sig = hmac.new(webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()

    with patch.object(settings, "RAZORPAY_WEBHOOK_SECRET", webhook_secret):
        resp = client.post(
            "/api/billing/webhook",
            content=raw_body,
            headers={"X-Razorpay-Signature": valid_sig, "Content-Type": "application/json"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Verify DB state
        sub = db_session.query(Subscription).filter(Subscription.user_id == user.id).first()
        assert sub is not None
        assert sub.status == "active"
        assert sub.razorpay_subscription_id == "sub_test_live_88"

        payment = db_session.query(Payment).filter(Payment.razorpay_payment_id == "pay_test_charge_2002").first()
        assert payment is not None
        assert payment.amount == 4900
        assert payment.status == "captured"


def test_webhook_idempotency_prevents_duplicate_processing(client, db_session):
    """Identical webhook delivered multiple times is handled idempotently without duplicate records."""
    user = db_session.query(User).filter(User.email == settings.DEMO_USER_EMAIL).first()
    webhook_secret = "webhook_secret_test_xyz"

    event_payload = {
        "event": "subscription.charged",
        "event_id": "evt_duplicate_test_9999",
        "payload": {
            "subscription": {
                "entity": {
                    "id": "sub_test_idemp_77",
                    "notes": {"user_id": str(user.id), "plan_code": "pro_monthly"},
                }
            },
            "payment": {
                "entity": {
                    "id": "pay_duplicate_test_8888",
                    "amount": 4900,
                    "currency": "USD",
                    "status": "captured",
                }
            },
        },
    }

    raw_body = json.dumps(event_payload).encode("utf-8")
    valid_sig = hmac.new(webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()

    with patch.object(settings, "RAZORPAY_WEBHOOK_SECRET", webhook_secret):
        # First delivery
        resp1 = client.post(
            "/api/billing/webhook",
            content=raw_body,
            headers={"X-Razorpay-Signature": valid_sig, "Content-Type": "application/json"},
        )
        assert resp1.status_code == 200
        assert resp1.json()["status"] == "processed"

        # Count records
        initial_payments_count = db_session.query(Payment).filter(Payment.razorpay_payment_id == "pay_duplicate_test_8888").count()
        assert initial_payments_count == 1

        # Second delivery (retry)
        resp2 = client.post(
            "/api/billing/webhook",
            content=raw_body,
            headers={"X-Razorpay-Signature": valid_sig, "Content-Type": "application/json"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "already_processed"

        # Verify no duplicate payments created
        after_payments_count = db_session.query(Payment).filter(Payment.razorpay_payment_id == "pay_duplicate_test_8888").count()
        assert after_payments_count == 1


def test_webhook_subscription_cancelled(client, db_session):
    """Cancelled webhook marks subscription as cancelled."""
    user = db_session.query(User).filter(User.email == settings.DEMO_USER_EMAIL).first()
    webhook_secret = "webhook_secret_test_xyz"

    event_payload = {
        "event": "subscription.cancelled",
        "event_id": "evt_cancel_555",
        "payload": {
            "subscription": {
                "entity": {
                    "id": "sub_cancel_123",
                    "notes": {"user_id": str(user.id)},
                }
            }
        },
    }

    raw_body = json.dumps(event_payload).encode("utf-8")
    valid_sig = hmac.new(webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()

    with patch.object(settings, "RAZORPAY_WEBHOOK_SECRET", webhook_secret):
        resp = client.post(
            "/api/billing/webhook",
            content=raw_body,
            headers={"X-Razorpay-Signature": valid_sig, "Content-Type": "application/json"},
        )
        assert resp.status_code == 200

        sub = db_session.query(Subscription).filter(Subscription.user_id == user.id).first()
        assert sub is not None
        assert sub.status == "cancelled"
        assert sub.cancelled_at is not None


def test_get_subscription_status(client, demo_auth_headers):
    """GET /api/billing/subscription returns user subscription and tier info."""
    resp = client.get("/api/billing/subscription", headers=demo_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "is_active" in data
    assert "tier_name" in data
    assert data["is_active"] is True


def test_cancel_subscription_endpoint(client, demo_auth_headers, db_session):
    """Authenticated cancellation endpoint marks subscription cancelled."""
    resp = client.post("/api/billing/cancel", headers=demo_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["status"] == "cancelled"


def test_protect_paid_feature_rejects_unsubscribed_user(client, second_user_auth_headers, db_session):
    """Free/unsubscribed user is blocked from premium features with HTTP 402."""
    user = db_session.query(User).filter(User.email == "alice@innovate.co").first()
    user.role = "Free Creator"
    db_session.commit()

    resp = client.post(
        "/api/repurpose",
        json={"raw_text": "This is a long piece of thought leadership content to repurpose into social formats.", "target_formats": ["linkedin"]},
        headers=second_user_auth_headers,
    )
    assert resp.status_code == 402
    assert "Active Pro Creator subscription required" in resp.json()["detail"]
