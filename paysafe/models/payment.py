"""
Payment models for the Paysafe Python SDK.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PaymentStatus(str, Enum):
    """Possible statuses for a payment."""
    
    CREATED = "CREATED"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    AUTHORIZED = "AUTHORIZED"
    SETTLING = "SETTLING"
    SETTLED = "SETTLED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"


class PaymentAddress(BaseModel):
    """Address model for payment-related addresses."""
    
    street: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = Field(..., min_length=2, max_length=2)
    zip: Optional[str] = None
    
    model_config = ConfigDict(
        validate_by_name=True
    )


class PaymentMethod(BaseModel):
    """Base class for payment methods."""
    
    type: str
    
    model_config = ConfigDict(
        validate_by_name=True
    )


class CardPaymentMethod(PaymentMethod):
    """Card payment method details."""
    
    type: str = "CARD"
    card_id: Optional[str] = None
    card_number: Optional[str] = None
    card_expiry: Optional[Dict[str, int]] = None
    card_holder_name: Optional[str] = None
    card_cvv: Optional[str] = None
    card_type: Optional[str] = None
    
    model_config = ConfigDict(
        validate_by_name=True
    )


class BankAccountPaymentMethod(PaymentMethod):
    """Bank account payment method details."""
    
    type: str = "BANK_ACCOUNT"
    account_id: Optional[str] = None
    account_number: Optional[str] = None
    routing_number: Optional[str] = None
    account_type: Optional[str] = None
    account_holder_name: Optional[str] = None
    
    model_config = ConfigDict(
        validate_by_name=True
    )


class Payment(BaseModel):
    """Model representing a payment in the Paysafe API."""
    
    id: Optional[str] = None
    merchant_reference_number: Optional[str] = None
    amount: int
    currency_code: str = Field(..., min_length=3, max_length=3)
    description: Optional[str] = None
    customer_id: Optional[str] = None
    payment_method: Union[CardPaymentMethod, BankAccountPaymentMethod]
    status: Optional[PaymentStatus] = None
    gateway_response: Optional[Dict[str, Any]] = None
    shipping_address: Optional[PaymentAddress] = None
    billing_address: Optional[PaymentAddress] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={"json_encoders": {datetime: lambda dt: dt.isoformat()}}
    )
    
    @field_validator('currency_code')
    def currency_code_uppercase(cls, v: str) -> str:
        """Ensure currency code is uppercase."""
        return v.upper()