from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ShipmentBase(BaseModel):
    date: Optional[datetime] = None
    type: Optional[str] = None
    product_name_list: Optional[List[str]] = None
    quantity_list: Optional[List[int]] = None
    supplier_name: Optional[str] = None
    status: Optional[str] = None
    expect_date: Optional[datetime] = None
    special_note: Optional[str] = None

class ShipmentCreate(ShipmentBase):
    pass

class ShipmentRead(ShipmentBase):
    id: int

    class Config:
        orm_mode = True

class ShipmentUpdate(ShipmentBase):
    pass