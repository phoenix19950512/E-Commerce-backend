from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class CustomersBase(BaseModel):
    mkt_id: Optional[int] = None
    name: Optional[str] = None
    company: Optional[str] = None
    gender: Optional[str] = None
    phone_1: Optional[str] = None
    billing_name: Optional[str] = None
    billing_phone: Optional[str] = None
    billing_country: Optional[str] = None
    billing_suburb: Optional[str] = None
    billing_city: Optional[str] = None
    billing_locality_id: Optional[str] = None
    billing_street: Optional[str] = None
    shipping_country: Optional[str] = None
    shipping_suburb: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_locality_id: Optional[str] = None  # JSON field to List[dict]
    shipping_contact: Optional[str] = None
    shipping_phone: Optional[str] = None
    shipping_street: Optional[str] = None
    created: Optional[datetime] = None  # Corrected to bool
    modified: Optional[datetime] = None
    legal_entity: Optional[int] = None
    is_vat_payer: Optional[int] = None
    market_place: Optional[str] = None
    code: Optional[str] = None
    bank: Optional[str] = None
    iban: Optional[str] = None
    email: Optional[str] = None
    registration_number: Optional[str] = None


class CustomersCreate(CustomersBase):
    pass

class CustomersUpdate(CustomersBase):
    pass

class CustomersRead(CustomersBase):
    id: int
    market_place: str

    class Config:
        orm_mode = True
