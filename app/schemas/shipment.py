from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ShipmentBase(BaseModel):
    title: Optional[str] = None
    date: Optional[datetime] = None
    type: Optional[str] = None
    status: Optional[str] = None
    warehouse: Optional[str] = None
    note: Optional[str] = None
    agent_name: Optional[str] = None
    ean: Optional[List[str]] = None
    quantity: Optional[List[int]] = None
    supplier_name: Optional[List[str]] = None
    item: Optional[List[int]] = None
    pdf_sent: Optional[List[bool]] = None
    pay_url: Optional[List[str]] = None
    tracking: Optional[List[str]] = None
    arrive_agent: Optional[List[bool]] = None
    wechat_group: Optional[List[str]] = None
    pp: Optional[List[str]] = None
    each_status: Optional[List[str]] = None
    shipment_name: Optional[List[str]] = None
    box_number: Optional[List[int]] = None
    document: Optional[List[str]] = None
    add_date: Optional[List[datetime]] = None
    date_agent: Optional[List[datetime]] = None
    SID: Optional[List[str]] = None
    GID: Optional[List[str]] = None
    date_port: Optional[List[datetime]] = None
    newid: Optional[List[str]] = None

class ShipmentCreate(ShipmentBase):
    pass

class ShipmentUpdate(ShipmentBase):
    pass

class ShipmentRead(ShipmentBase):
    id: int

    class Config:
        orm_mode = True