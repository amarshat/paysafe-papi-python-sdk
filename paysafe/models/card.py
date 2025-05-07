"""
Card models for the Paysafe Python SDK.
"""

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, validator


class CardType(str, Enum):
    """Supported card types."""
    
    VISA = "VISA"
    MASTERCARD = "MASTERCARD"
    AMEX = "AMEX"
    DISCOVER = "DISCOVER"
    JCB = "JCB"
    DINERS = "DINERS"
    UNKNOWN = "UNKNOWN"


class CardExpiry(BaseModel):
    """Card expiry data model."""
    
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=0, le=99)
    
    class Config:
        """Pydantic model configuration."""
        
        allow_population_by_field_name = True
    
    @validator('year')
    def validate_year(cls, v: int) -> int:
        """Validate that the year is in a valid format."""
        # Allow both 2-digit and 4-digit years
        if v > 99:
            v = v % 100
        return v


class CardStatus(str, Enum):
    """Possible statuses for a card."""
    
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXPIRED = "EXPIRED"
    BLOCKED = "BLOCKED"


class Card(BaseModel):
    """Model representing a card in the Paysafe API."""
    
    id: Optional[str] = None
    customer_id: Optional[str] = None
    card_type: Optional[CardType] = None
    card_number: Optional[str] = None
    card_bin: Optional[str] = None
    last_digits: Optional[str] = None
    holder_name: Optional[str] = None
    expiry: Optional[CardExpiry] = None
    cvv: Optional[str] = None
    status: Optional[CardStatus] = CardStatus.ACTIVE
    billing_address_id: Optional[str] = None
    nick_name: Optional[str] = None
    default: Optional[bool] = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    payment_token: Optional[str] = None
    
    class Config:
        """Pydantic model configuration."""
        
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
    
    @validator('card_number')
    def mask_card_number(cls, v: Optional[str]) -> Optional[str]:
        """
        Mask the card number for security.
        
        This validator will replace all but the last 4 digits with asterisks.
        """
        if not v:
            return v
            
        if len(v) <= 4:
            return v
            
        masked = '*' * (len(v) - 4) + v[-4:]
        return masked
