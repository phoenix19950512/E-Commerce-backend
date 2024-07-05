from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean, JSON, ARRAY, Numeric
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import relationship
# from sqlalchemy.dialects.postgresql import UUID
# import uuid
from app.database import Base
from app.models.product import Product

from sqlalchemy.orm import relationship

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    vendor_name = Column(String, nullable=True)
    type = Column(Integer, nullable=True)
    parent_id = Column(Integer, nullable=True)
    date = Column(DateTime, nullable=True)
    payment_mode = Column(String, nullable=True)
    detailed_payment_method = Column(String, nullable=True)
    delivery_mode = Column(String, nullable=True)
    observation = Column(String, nullable=True)
    status = Column(Integer, nullable=True)
    payment_status = Column(Integer, nullable=True)
    customer_id = Column(Integer, nullable=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    shipping_tax = Column(Float, nullable=True)
    shipping_tax_voucher_split = Column(String, nullable=True)
    vouchers = Column(String, nullable=True)
    proforms = Column(String, nullable=True)
    attachments = Column(JSON, nullable=True)
    cashed_co = Column(Float, nullable=True)
    cashed_cod = Column(Float, nullable=True)
    cancellation_request = Column(String, nullable=True)
    has_editable_products = Column(Boolean, nullable=True)
    refunded_amount = Column(Integer, nullable=True)
    is_complete = Column(Boolean, nullable=True)
    reason_cancellation = Column(String, nullable=True)
    refund_status = Column(String, nullable=True)
    maximum_date_for_shipment = Column(DateTime, nullable=True)
    late_shipment = Column(Integer, nullable=True)
    flags = Column(JSON, nullable=True)
    emag_club = Column(Boolean, nullable=True)
    finalization_date = Column(DateTime, nullable=True)
    details = Column(JSON, nullable=True)
    weekend_delivery = Column(Boolean, nullable=True)
    payment_mode_id = Column(Integer, nullable=True)
    sales = Column(Numeric(16, 4), nullable=True)
    unit = Column(Integer, nullable=True)
    gross_profit = Column(Numeric(16, 4), nullable=True)
    net_profit = Column(Numeric(16, 4), nullable=True)

    owner = relationship('Product', back_populates='orders')

Product.orders = relationship('Order', back_populates='owner')

