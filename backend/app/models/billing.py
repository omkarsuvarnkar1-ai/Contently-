from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


def utcnow():
    return datetime.now(UTC)


class Subscription(Base):
    """Stores user subscription states, synced authoritatively via Razorpay webhooks."""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    plan_code = Column(String(50), nullable=False, default="pro_monthly")
    plan_name = Column(String(100), nullable=False, default="Pro Creator Tier")

    # Subscription status: active, authenticated, pending, past_due, halted, cancelled, free
    status = Column(String(50), nullable=False, default="active", index=True)

    # Razorpay IDs
    razorpay_subscription_id = Column(String(100), nullable=True, index=True)
    razorpay_plan_id = Column(String(100), nullable=True)
    razorpay_customer_id = Column(String(100), nullable=True)

    # Billing lifecycle dates
    current_start = Column(DateTime, nullable=True)
    current_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    cancelled_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    user = relationship("User", back_populates="subscription")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")


class Payment(Base):
    """Tracks individual payment transactions and invoice settlements."""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)

    razorpay_payment_id = Column(String(100), unique=True, index=True, nullable=False)
    razorpay_order_id = Column(String(100), nullable=True, index=True)
    razorpay_signature = Column(String(255), nullable=True)

    amount = Column(Integer, nullable=False)  # in smallest currency unit (paise or cents)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(50), nullable=False)  # captured, authorized, failed, refunded
    method = Column(String(50), nullable=True)  # card, upi, netbanking, etc.

    error_code = Column(String(100), nullable=True)
    error_description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utcnow)

    # Relationships
    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")


class WebhookEvent(Base):
    """Idempotency ledger for incoming Razorpay webhook events."""
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), unique=True, index=True, nullable=False)
    event_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default="processed", nullable=False)
    payload = Column(Text, nullable=True)
    processed_at = Column(DateTime, default=utcnow)
