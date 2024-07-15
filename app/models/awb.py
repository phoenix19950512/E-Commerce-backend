# app/models/awb.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class AWB(Base):
    __tablename__ = "awbs"
    
    id = Column(Integer, primary_key=True, index=True)
    awb_number = Column(String, unique=True, index=True, nullable=False)
    order_id = Column(Integer, nullable=False)
    observation_field = Column(String, nullable=True)

