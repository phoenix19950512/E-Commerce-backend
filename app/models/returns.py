from sqlalchemy import Column, Integer, String, PrimaryKeyConstraint, BigInteger, ARRAY, DateTime
from app.database import Base

class Returns(Base):
    __tablename__ = "returns"
    emag_id = Column(BigInteger, nullable=True)
    order_id = Column(BigInteger, primary_key=True)
    type = Column(Integer, nullable=True)
    customer_name = Column(String, nullable=True)
    customer_company = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    products = Column(ARRAY(Integer), nullable=True)
    quantity = Column(ARRAY(Integer), nullable=True)
    pickup_address = Column(String, nullable=True)
    return_reason = Column(String, nullable=True)
    return_type = Column(Integer, nullable=True)
    replacement_product_emag_id = Column(Integer, nullable=True)
    replacement_product_id = Column(Integer, nullable=True)
    replacement_product_name = Column(String, nullable=True)
    replacement_product_quantity = Column(Integer, nullable=True)
    date = Column(DateTime, nullable=True)
    request_status = Column(Integer, nullable=True)
    return_market_place = Column(String, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint('order_id', 'return_market_place', name='pk_order_id_return_market_place'),
    )