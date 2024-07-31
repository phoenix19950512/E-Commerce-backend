# app/models/awb.py
from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base


class AWB(Base):
    __tablename__ = "awbs"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, unique=True, index=True, nullable=False)
    sender_name = Column(String, nullable=True)
    sender_phone1 = Column(String, nullable=True)
    sender_phone2 = Column(String, nullable=True)
    sender_locality_id = Column(BigInteger, nullable=True)
    sender_street = Column(String, nullable=True)
    sender_zipcode = Column(String, nullable=True)
    receiver_name = Column(String, nullable=True)
    receiver_contact = Column(String, nullable=True)
    receiver_phone1 = Column(String, nullable=True)
    receiver_phone2 = Column(String, nullable=True)
    receiver_legal_entity = Column(Boolean, nullable=True)
    receiver_locality_id = Column(BigInteger, nullable=True)
    receiver_street = Column(String, nullable=True)
    receiver_zipcode = Column(String, nullable=True)
    locker_id = Column(String, nullable=True)
    is_oversize = Column(Boolean, nullable=True)
    insured_value = Column(DECIMAL, nullable=True) 
    weight = Column(DECIMAL, nullable=True)
    envelope_number = Column(Integer, nullable=False)
    parcel_number = Column(Integer, nullable=True)
    observation = Column(String, nullable=True)
    cod = Column(DECIMAL, nullable=True)
    courier_account_id = Column(Integer, nullable=True)
    pickup_and_return = Column(Boolean, nullable=True)
    saturday_delivery = Column(Boolean, nullable=True)
    sameday_delivery = Column(Boolean, nullable=True)
    dropoff_locker = Column(Boolean, nullable=True)