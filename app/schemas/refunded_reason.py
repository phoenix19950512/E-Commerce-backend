from pydantic import BaseModel
from typing import Optional

class RefundedReasonBase(BaseModel):
    refunded_reason: Optional[str] = None

class RefundedReasonCreate(RefundedReasonBase):
    pass

class RefundedReasonRead(RefundedReasonBase):
    id: int

    class Config:
        orm_mode = True

class RefundedReasonUpdate(RefundedReasonBase):
    pass