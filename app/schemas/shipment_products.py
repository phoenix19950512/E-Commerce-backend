
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ShipmentProductBase(BaseModel):
    shipment_id: Optional[int] = None
    name: Optional[str] = None
    ean: Optional[str] = None
    quantity: Optional[int] = None
    supplier_name: Optional[List[str]] = None
    item: Optional[int] = None
    pdf_sent: Optional[bool] = None
    pay_url: Optional[str] = None
    tracking: Optional[str] = None
    arrive_agent: Optional[bool] = None
    wechat_group: Optional[str] = None
    pp: Optional[str] = None
    each_status: Optional[str] = None
    shipment_name: Optional[str] = None
    box_number: Optional[int] = None
    document: Optional[str] = None
    barcode_url: Optional[str] = None
    add_date: Optional[datetime] = None
    date_agent: Optional[datetime] = None
    SID: Optional[str] = None
    GID: Optional[str] = None
    date_port: Optional[datetime] = None
    newid: Optional[str] = None

class ShipmentProductCreate(ShipmentProductBase):
    pass

class ShipmentProductUpdate(ShipmentProductBase):
    pass

class ShipmentProductRead(ShipmentProductBase):
    id: int

    class Config:
        orm_mode = True