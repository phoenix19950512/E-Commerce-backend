from sqlalchemy import Column, Integer, String, PrimaryKeyConstraint, DateTime
from app.database import Base


class Scan_awb(Base):
    __tablename__ = 'scan_awbs'
    id = Column(Integer, primary_key=True)
    awb_number = Column(String, nullable=True)
    awb_type = Column(String, nullable=True)
    scan_date = Column(DateTime, nullable=True)
    user_id = Column(Integer, nullable=True)
    __table_args__ = (
        PrimaryKeyConstraint('account_id', 'market_place', name='pk_account_id_market_place'),
    )

