from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean, JSON, Numeric, ARRAY
from app.database import Base
from sqlalchemy.orm import relationship
from app.models.product import Product

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    vendor_name = Column(String, nullable=True)
    type = Column(Integer, nullable=True)
    date = Column(DateTime, nullable=True)
    payment_mode = Column(String, nullable=True)
    detailed_payment_method = Column(String, nullable=True)
    delivery_mode = Column(String, nullable=True)
    status = Column(Integer, nullable=True)
    payment_status = Column(Integer, nullable=True)
    customer_id = Column(Integer, nullable=True)
    product_id = Column(ARRAY(Integer), nullable=True)
    quantity = Column(ARRAY(Integer), nullable=True)
    shipping_tax = Column(Float, nullable=True)
    shipping_tax_voucher_split = Column(String, nullable=True)
    vouchers = Column(String, nullable=True)
    proforms = Column(String, nullable=True)
    attachments = Column(JSON, nullable=True)
    cashed_co = Column(Float, nullable=True)
    cashed_cod = Column(Float, nullable=True)
    refunded_amount = Column(Integer, nullable=True)
    is_complete = Column(Boolean, nullable=True)
    cancellation_reason = Column(Integer, nullable=True)
    refund_status = Column(String, nullable=True)
    maximum_date_for_shipment = Column(DateTime, nullable=True)
    late_shipment = Column(Integer, nullable=True)
    flags = Column(JSON, nullable=True)
    emag_club = Column(Boolean, nullable=True)
    finalization_date = Column(DateTime, nullable=True)
    details = Column(JSON, nullable=True)
    payment_mode_id = Column(Integer, nullable=True)

