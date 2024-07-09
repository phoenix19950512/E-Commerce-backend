from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, VARCHAR, DateTime, JSON
from app.database import Base

class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=True)
    type = Column(String, nullable=True)
    product_name_list = Column(JSON, nullable=True)
    quantity_list = Column(JSON, nullable=True)
    supplier_name = Column(String, nullable=True)
    status = Column(String, nullable=True)
    expect_date = Column(DateTime, nullable=True)
    special_note = Column(String, nullable=True)