from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, VARCHAR
from app.database import Base

class RefundedReason(Base):
    __tablename__ = "refunded_reasons"

    id = Column(Integer, primary_key=True, index=True)
    refunded_reason = Column(String, nullable=True)