from pydantic import BaseModel, HttpUrl, EmailStr
from typing import Dict
from typing import Optional
from datetime import datetime

class NotificationBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    time: Optional[datetime] = None
    state: str = 'warning'
    read: bool = False
    user_id: int = 1

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(NotificationBase):
    pass

class NotificationRead(NotificationBase):
    id: int

    class Config:
        orm_mode = True
        from_attributes = True
