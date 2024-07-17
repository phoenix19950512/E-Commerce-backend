from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class RefundedBase(BaseModel):
    emag_id: Optional[int] = None
    order_id: int
    type: Optional[int] = None
    customer_name: Optional[str] = None
    customer_company: Optional[str] = None
    customer_phone: Optional[str] = None
    products: Optional[List[int]] = None
    quantity: Optional[List[int]] = None
    pickup_address: Optional[str] = None
    return_reason: Optional[int] = None
    return_type: Optional[int] = None
    replacement_product_emag_id: Optional[int] = None
    replacement_product_id: Optional[int] = None
    replacement_product_name: Optional[str] = None
    replacement_product_quantity: Optional[int] = None
    date: Optional[datetime] = None
    request_status: Optional[int] = None
    market_place: Optional[str] = None

class RefundedCreate(RefundedBase):
    pass

class RefundedRead(RefundedBase):
    order_id: int

    class Config:
        orm_mode = True

class RefundedUpdate(RefundedBase):
    pass