from sqlalchemy import Column, Integer, String, PrimaryKeyConstraint, BigInteger, DateTime
from app.database import Base


class Customers(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    mkt_id = Column(BigInteger, nullable=True)
    name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    phone_1 = Column(String, nullable=True)
    billing_name = Column(String, nullable=True)
    billing_phone = Column(String, nullable=True)
    billing_country = Column(String, nullable=True)
    billing_suburb = Column(String, nullable=True)
    billing_city = Column(String, nullable=True)
    billing_locality_id = Column(String, nullable=True)
    billing_street = Column(String, nullable=True)
    shipping_country = Column(String, nullable=True)
    shipping_suburb = Column(String, nullable=True)
    shipping_city = Column(String, nullable=True)
    shipping_locality_id = Column(String, nullable=True)
    shipping_contact = Column(String, nullable=True)
    shipping_phone = Column(String, nullable=True)
    shipping_street = Column(String, nullable=True)
    created = Column(DateTime, nullable=True)
    modified = Column(DateTime, nullable=True)
    legal_entity = Column(Integer, nullable=True)
    is_vat_payer = Column(Integer, nullable=True)
    market_place = Column(String, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint('id', 'market_place', name='pk_id_market_place'),
    )

