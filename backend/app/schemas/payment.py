from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class InitializePaymentRequest(BaseModel):
    plan: str = "premium_monthly"


class InitializePaymentResponse(BaseModel):
    authorization_url: str
    reference: str


class SubscriptionStatusOut(BaseModel):
    plan: Optional[str]
    status: str  # mirrors user.subscription_status: free | active | expired
    expires_at: Optional[datetime]


class VerifyPaymentResponse(BaseModel):
    status: str  # Paystack transaction state, or "active" once we've activated
    subscription_status: str  # the user's resulting subscription_status


class MarkPaidRequest(BaseModel):
    email: str
