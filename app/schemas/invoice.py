from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InvoicesBase(BaseModel):
    order_id: Optional[int] = None
    companyVatCode: Optional[str] = None
    seriesName: Optional[str] = None
    client: Optional[str] = None
    issueDate: Optional[datetime] = None
    products: Optional[str] = None
    number: Optional[str] = None
    series: Optional[str] = None
    url: Optional[str] = None
    
class InvoicesCreate(InvoicesBase):
    pass

class InvoicesRead(InvoicesBase):
    id:int

    class Config:
        orm_mode = True

class InvoicesUpdate(InvoicesBase):
    pass