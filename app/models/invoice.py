from sqlalchemy import Column, Integer, Text, DateTime, ARRAY, Numeric, Boolean
from app.database import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, nullable=True)
    companyVatCode = Column(Integer, nullable=True)
    seriesName = Column(Text, nullable=True)
    client = Column(Text, nullable=True)
    issueDate = Column(DateTime, nullable=True)
    products = Column(Text, nullable=True)
    number = Column(Text, nullable=True)
    series = Column(Text, nullable=True)
    url = Column(Text, nullable=True)

    