from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, VARCHAR, DateTime
from app.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    time = Column(DateTime, nullable=True)
    state = Column(Text, nullable=False)
    read = Column(Boolean, nullable=False)
    user_id = Column(Integer, nullable=False)