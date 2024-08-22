from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class ReplacementsBase(BaseModel):
    id: int
    order_id: Optional[int] = None
    date: Optional[datetime] = None
    product_ean: Optional[List[str]] = None
    marketplace: Optional[str] = None
    reason: Optional[str] = None
    awb: Optional[str] = None
    total: Optional[Decimal] = None
    status: Optional[int] = None
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    customer_email: Optional[str] = None
    review:Optional[bool] = None
    
class ReplacementsCreate(ReplacementsBase):
    pass

class ReplacementsRead(ReplacementsBase):
    id:int

    class Config:
        orm_mode = True

class ReplacementsUpdate(ReplacementsBase):
    pass