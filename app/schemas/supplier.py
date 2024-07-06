from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class SupplierBase(BaseModel):
    supplier_group: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_wechat: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class SupplierRead(SupplierBase):
    id: int

    class Config:
        orm_mode = True

class SupplierUpdate(SupplierBase):
    pass