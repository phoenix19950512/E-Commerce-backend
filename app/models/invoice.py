from sqlalchemy import Column, Integer, Text, DateTime, ARRAY, Numeric, Boolean
from app.database import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, nullable=True)
    companyVatCode = Column(Text, nullable=True)
    seriesName = Column(Text, nullable=True)
    client = Column(Text, nullable=True)
    usestock = Column(Boolean, nullable=True)
    isdraft = Column(Boolean, nullable=True)
    issueDate = Column(DateTime, nullable=True)
    mentions = Column(Text, nullable=True)
    observations = Column(Text, nullable=True)
    language = Column(Text, nullable=True)
    precision = Column(Integer, nullable=True)
    useEstimateDetails = Column(Boolean, nullable=True)
    estimate = Column(Text, nullable=True)
    currency = Column(Text, nullable=True)
    products = Column(Text, nullable=True)
    number = Column(Text, nullable=True)
    series = Column(Text, nullable=True)
    url = Column(Text, nullable=True)

    