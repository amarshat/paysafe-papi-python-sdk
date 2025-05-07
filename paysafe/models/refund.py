"""
Refund models for the Paysafe Python SDK.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class RefundStatus(str, Enum):
    """Possible statuses for a refund."""
    
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Refund(BaseModel):
    """Model representing a refund in the Paysafe API."""
    
    id: Optional[str] = None
    payment_id: str
    merchant_reference_number: Optional[str] = None
    amount: int
    currency_code: str = Field(..., min_length=3, max_length=3)
    status: Optional[RefundStatus] = None
    reason: Optional[str] = None
    gateway_response: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        """Pydantic model configuration."""
        
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
