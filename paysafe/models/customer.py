"""
Customer models for the Paysafe Python SDK.
"""

from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CustomerStatus(str, Enum):
    """Possible statuses for a customer."""
    
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCKED = "BLOCKED"


class CustomerBillingDetails(BaseModel):
    """Model representing customer billing details."""
    
    street: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    zip: Optional[str] = None
    phone: Optional[str] = None
    
    model_config = ConfigDict(
        validate_by_name=True
    )


class Customer(BaseModel):
    """Model representing a customer in the Paysafe API."""
    
    id: Optional[str] = None
    merchant_customer_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    billing_details: Optional[CustomerBillingDetails] = None
    status: Optional[CustomerStatus] = CustomerStatus.ACTIVE
    locale: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={"json_encoders": {datetime: lambda dt: dt.isoformat()}}
    )
    
    def get_full_name(self) -> str:
        """
        Get the customer's full name.
        
        Returns:
            The customer's full name, or an empty string if no name is available.
        """
        first = self.first_name or ""
        last = self.last_name or ""
        
        if first and last:
            return f"{first} {last}"
        elif first:
            return first
        elif last:
            return last
        else:
            return ""