from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class Team_memberBase(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    last_logged_in: Optional[datetime] = None
    hashed_password: Optional[str] = None

class Team_memberCreate(Team_memberBase):
    pass

class Team_memberRead(Team_memberBase):
    id: int
    class Config:
        orm_mode = True
        from_attributes = True


class Team_memberUpdate(Team_memberBase):
    pass
