from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class OrderBase(BaseModel):
    vendor_name: Optional[str] = None
    type: Optional[int] = None
    parent_id: Optional[int] = None
    date: Optional[datetime] = None
    payment_mode: Optional[str] = None
    detailed_payment_method: Optional[str] = None
    delivery_mode: Optional[str] = None
    observation: Optional[str] = None
    status: Optional[int] = None
    payment_status: Optional[int] = None
    customer_id: Optional[int] = None
    product_id: Optional[int] = None
    shipping_tax: Optional[float] = None
    shipping_tax_voucher_split: Optional[str] = None
    vouchers: Optional[str] = None
    proforms: Optional[str] = None
    attachments: Optional[List[dict]] = None  # JSON field to List[dict]
    cashed_co: Optional[float] = None
    cashed_cod: Optional[float] = None
    has_editable_products: Optional[bool] = None  # Corrected to bool
    refunded_amount: Optional[int] = None
    is_complete: Optional[bool] = None  # Corrected to bool
    refunded_reason_id: Optional[int] = None
    refund_status: Optional[str] = None
    maximum_date_for_shipment: Optional[datetime] = None
    late_shipment: Optional[int] = None
    flags: Optional[List[dict]] = None  # JSON field to List[dict]
    emag_club: Optional[bool] = None  # Corrected to bool
    finalization_date: Optional[datetime] = None
    details: Optional[List[dict]] = None  # JSON field to List[dict]
    weekend_delivery: Optional[bool] = None  # Corrected to bool
    payment_mode_id: Optional[int] = None
    sales: Optional[Decimal] = None
    unit: Optional[int] = None
    gross_profit: Optional[Decimal] = None
    net_profit: Optional[Decimal] = None

class OrderCreate(OrderBase):
    pass

class OrderUpdate(OrderBase):
    pass

class OrderRead(OrderBase):
    id: int

    class Config:
        orm_mode = True
        from_attributes = True
