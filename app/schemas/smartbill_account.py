from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class Smartbill_accountsBase(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    cif_info: Optional[str] = None
    
class Smartbill_accountsCreate(Smartbill_accountsBase):
    pass

class Smartbill_accountsRead(Smartbill_accountsBase):
    id:int

    class Config:
        orm_mode = True

class Smartbill_accountsUpdate(Smartbill_accountsBase):
    pass