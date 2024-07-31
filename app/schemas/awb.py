# app/schemas/awb.py
from pydantic import BaseModel
from enum import Enum
from typing import Optional
from decimal import Decimal

class AWBBase(BaseModel):
    order_id: int
    sender_name: Optional[str] = None
    sender_phone1: Optional[str] = None
    sender_phone2: Optional[str] = None
    sender_locality_id: Optional[int] = None
    sender_street: Optional[str] = None
    sender_zipcode: Optional[str] = None
    receiver_name: Optional[str] = None
    receiver_contact: Optional[str] = None
    receiver_phone1: Optional[str] = None
    receiver_phone2: Optional[str] = None
    receiver_legal_entity: Optional[bool] = None
    receiver_locality_id: Optional[int] = None
    receiver_street: Optional[str] = None
    receiver_zipcode: Optional[str] = None
    locker_id: Optional[str] = None
    is_oversize: Optional[bool] = None
    insured_value: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    envelope_number: Optional[int] = None
    parcel_number: Optional[int] = None
    observation: Optional[str] = None
    cod: Optional[Decimal] = None
    courier_account_id: Optional[int] = None
    pickup_and_return: Optional[bool] = None
    saturday_delivery: Optional[bool] = None
    sameday_delivery: Optional[bool] = None
    dropoff_locker: Optional[bool] = None

class AWBCreate(AWBBase):
    pass

class AWBUpdate(AWBBase):
    pass

class AWBRead(AWBBase):
    id: int

    class Config:
        orm_mode = True

# class ObservationFieldEnum(str, Enum):
#     EAN = "EAN"
#     SKU = "SKU"
#     EAN_SKU = "EAN_SKU"

# class AWBCreate(AWBBase):
#     observation_field: ObservationFieldEnum
