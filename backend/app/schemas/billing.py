from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PlanItem(BaseModel):
    id: str
    name: str
    tier_name: str
    interval: str
    price_usd: float
    price_inr: float
    amount_usd_cents: int
    amount_inr_paise: int
    description: str
    features: list[str]


class PlanCatalogResponse(BaseModel):
    plans: list[PlanItem]
    active_currency: str


class CheckoutRequest(BaseModel):
    plan_code: str = Field(default="pro_monthly", description="Plan code: pro_monthly or pro_yearly")
    currency: str | None = Field(default=None, description="Optional currency override: USD or INR")


class CheckoutResponse(BaseModel):
    key_id: str
    subscription_id: str | None = None
    order_id: str | None = None
    amount: int
    currency: str
    plan_code: str
    plan_name: str
    tier_name: str
    billing_interval: str
    prefill: dict[str, str]
    notes: dict[str, Any]
    checkout_type: str  # 'subscription' or 'order'


class VerifyPaymentRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_subscription_id: str | None = None
    razorpay_order_id: str | None = None
    razorpay_signature: str
    plan_code: str | None = "pro_monthly"


class VerifyPaymentResponse(BaseModel):
    success: bool
    status: str
    message: str
    payment_id: str | None = None
    subscription_status: str | None = None


class PaymentHistoryItem(BaseModel):
    id: int
    razorpay_payment_id: str
    amount: int
    currency: str
    status: str
    method: str | None = None
    created_at: datetime


class SubscriptionResponse(BaseModel):
    status: str
    is_active: bool
    plan_code: str | None = None
    plan_name: str | None = None
    tier_name: str
    current_start: datetime | None = None
    current_end: datetime | None = None
    cancel_at_period_end: bool = False
    cancelled_at: datetime | None = None
    recent_payments: list[PaymentHistoryItem] = []


class CancelSubscriptionResponse(BaseModel):
    success: bool
    status: str
    message: str
