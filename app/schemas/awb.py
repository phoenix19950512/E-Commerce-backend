# app/schemas/awb.py
from pydantic import BaseModel
from enum import Enum

class AWBBase(BaseModel):
    order_id: int
    observation_field: str

class AWBCreate(AWBBase):
    pass

class AWBRead(AWBBase):
    id: int
    awb_number: str

    class Config:
        orm_mode = True

class ObservationFieldEnum(str, Enum):
    EAN = "EAN"
    SKU = "SKU"
    EAN_SKU = "EAN_SKU"

class AWBCreate(AWBBase):
    observation_field: ObservationFieldEnum
