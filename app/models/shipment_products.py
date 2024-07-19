from sqlalchemy import Column, Integer, ARRAY, Text, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Shipmentprodcut(Base):
    __tablename__ = "shipment_products"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shipment_id = Column(Integer, nullable=False)
    name = Column(Text, nullable=True)
    ean = Column(Text, nullable=True)
    quantity = Column(Integer, nullable=True)
    supplier_name = Column(ARRAY(Text), nullable=True)
    item = Column(Integer, nullable=True)
    pdf_sent = Column(Boolean, nullable=True)
    pay_url = Column(Text, nullable=True)
    tracking = Column(Text, nullable=True)
    arrive_agent = Column(Boolean, nullable=True)
    wechat_group = Column(Text, nullable=True)
    pp = Column(Text, nullable=True)
    each_status = Column(Text, nullable=True)
    shipment_name = Column(Text, nullable=True)
    box_number = Column(Integer, nullable=True)
    document = Column(Text, nullable=True)
    barcode_url = Column(Text, nullable=True)
    add_date = Column(DateTime, nullable=True)
    date_agent = Column(DateTime, nullable=True)
    SID = Column(Text, nullable=True)
    GID = Column(Text, nullable=True)
    date_port = Column(DateTime, nullable=True)
    newid = Column(Text, nullable=True)