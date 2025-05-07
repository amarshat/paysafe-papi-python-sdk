"""
Webhook models for the Paysafe Python SDK.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from pydantic import BaseModel, AnyHttpUrl, Field


class WebhookEvent(str, Enum):
    """Types of events that can trigger a webhook."""
    
    PAYMENT_CREATED = "payment.created"
    PAYMENT_PENDING = "payment.pending"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_CANCELLED = "payment.cancelled"
    PAYMENT_REFUNDED = "payment.refunded"
    
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    CUSTOMER_DELETED = "customer.deleted"
    
    CARD_CREATED = "card.created"
    CARD_UPDATED = "card.updated"
    CARD_DELETED = "card.deleted"
    
    REFUND_CREATED = "refund.created"
    REFUND_COMPLETED = "refund.completed"
    REFUND_FAILED = "refund.failed"


class Webhook(BaseModel):
    """Model representing a webhook subscription in the Paysafe API."""
    
    id: Optional[str] = None
    url: AnyHttpUrl
    events: List[WebhookEvent]
    description: Optional[str] = None
    active: bool = True
    secret: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        """Pydantic model configuration."""
        
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class WebhookPayload(BaseModel):
    """Model representing a webhook event payload."""
    
    id: str
    event: WebhookEvent
    created_at: datetime
    data: Dict[str, Any]
    
    class Config:
        """Pydantic model configuration."""
        
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
