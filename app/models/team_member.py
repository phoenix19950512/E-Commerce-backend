from sqlalchemy import Column, Integer, ARRAY
from app.database import Base
from datetime import datetime
class Team_member(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    member_id = Column(ARRAY(Integer), nullable=True)
    