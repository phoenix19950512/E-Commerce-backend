from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, any_
from typing import List
from app.database import get_db
from app.models.smartbill_account import Smartbill_account
from app.schemas.smartbill_account import Smartbill_accountsCreate, Smartbill_accountsRead, Smartbill_accountsUpdate

router = APIRouter()

@router.post("/", response_model=Smartbill_accountsRead)
async def create_smartbill_account(smartbill_account: Smartbill_accountsCreate, db: AsyncSession = Depends(get_db)):
    db_smartbill_account = Smartbill_account(**smartbill_account.dict())
    db.add(db_smartbill_account)
    await db.commit()
    await db.refresh(db_smartbill_account)
    return db_smartbill_account

@router.get('/count')
async def get_smartbill_account_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(func.count(Smartbill_account.id))
    count = result.scalar()
    return count

@router.get("/{user_id}", response_model=Smartbill_accountsRead)
async def get_smartbill_account(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Smartbill_account).filter(Smartbill_account.user_id == user_id))
    db_smartbill_account = result.scalars().first()
    return db_smartbill_account

@router.put("/{smartbill_account_id}", response_model=Smartbill_accountsRead)
async def update_smartbill_account(smartbill_account_id: int, smartbill_account: Smartbill_accountsUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Smartbill_account).filter(Smartbill_account.id == smartbill_account_id))
    db_smartbill_account = result.scalars().first()
    if db_smartbill_account is None:
        raise HTTPException(status_code=404, detail="smartbill_account not found")
    for var, value in vars(smartbill_account).items():
        setattr(db_smartbill_account, var, value) if value else None
    await db.commit()
    await db.refresh(db_smartbill_account)
    return db_smartbill_account

@router.delete("/{smartbill_account_id}", response_model=Smartbill_accountsRead)
async def delete_smartbill_account(smartbill_account_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Smartbill_account).filter(Smartbill_account.id == smartbill_account_id))
    smartbill_account = result.scalars().first()
    if smartbill_account is None:
        raise HTTPException(status_code=404, detail="smartbill_account not found")
    await db.delete(smartbill_account)
    await db.commit()
    return smartbill_account
