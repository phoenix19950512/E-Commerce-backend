from sqlalchemy import Column, Integer, Text
from app.database import Base

class Smartbill_account(Base):
    __tablename__ = "smartbill_accounts"
    id = Column(Integer, primary_key=True, autoincrement=True)  # Ensure id is a primary key and auto-incrementing
    user_id = Column(Integer, nullable=True)  
    username = Column(Text, nullable=True)
    password = Column(Text, nullable=True)
    cif_info = Column(Text, nullable=True)
    

