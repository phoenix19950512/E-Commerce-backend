from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class OrderBase(BaseModel):
    vendor_name: Optional[str] = None
    type: Optional[int] = None
    date: Optional[datetime] = None
    payment_mode: Optional[str] = None
    detailed_payment_method: Optional[str] = None
    delivery_mode: Optional[str] = None
    status: Optional[int] = None
    payment_status: Optional[int] = None
    customer_id: Optional[int] = None
    product_id: Optional[List[str]] = None
    quantity: Optional[List[int]] = None
    sale_price: Optional[List[float]] = None
    shipping_tax: Optional[float] = None
    shipping_tax_voucher_split: Optional[str] = None
    vouchers: Optional[str] = None
    proforms: Optional[str] = None
    attachments: Optional[str] = None  # JSON field to List[dict]
    shipping_address: Optional[str] = None
    cashed_co: Optional[float] = None
    cashed_cod: Optional[float] = None
    refunded_amount: Optional[float] = None
    is_complete: Optional[int] = None  # Corrected to bool
    cancellation_request: Optional[str] = None
    cancellation_reason: Optional[str] = None
    refund_status: Optional[str] = None
    maximum_date_for_shipment: Optional[datetime] = None
    late_shipment: Optional[int] = None
    flags: Optional[str] = None  # JSON field to List[dict]
    emag_club: Optional[int] = None  # Corrected to bool
    finalization_date: Optional[datetime] = None
    details: Optional[str] = None  # JSON field to List[dict]
    payment_mode_id: Optional[int] = None
    order_market_place: Optional[str] = None


class OrderCreate(OrderBase):
    pass

class OrderUpdate(OrderBase):
    pass

class OrderRead(OrderBase):
    id: int
    order_market_place: str

    class Config:
        orm_mode = True
