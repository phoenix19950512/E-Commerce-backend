from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, any_
from typing import List
from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.models.billing_software import Billing_software
from app.schemas.billing_software import Billing_softwaresCreate, Billing_softwaresRead, Billing_softwaresUpdate

router = APIRouter()

@router.post("/", response_model=Billing_softwaresRead)
async def create_billing_software(billing_software: Billing_softwaresCreate, db: AsyncSession = Depends(get_db)):
    db_billing_software = Billing_software(**billing_software.dict())
    db.add(db_billing_software)
    await db.commit()
    await db.refresh(db_billing_software)
    return db_billing_software

@router.get('/count')
async def get_billing_software_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(func.count(Billing_software.id))
    count = result.scalar()
    return count

@router.get("/", response_model=List[Billing_softwaresRead])
async def get_billing_softwares(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Billing_software))
    db_billing_softwares = result.scalars().all()

    if db_billing_softwares is None:
        raise HTTPException(status_code=404, detail="Billing Software not found")
    
    return db_billing_softwares

@router.get("/{user_id}", response_model=Billing_softwaresRead)
async def get_billing_software(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Billing_software).filter(Billing_software.user_id == user_id))
    db_billing_software = result.scalars().first()
    if db_billing_software is None:
        raise HTTPException(status_code=404, detail="Billing Software not found")
    return db_billing_software

@router.put("/{billing_software_id}", response_model=Billing_softwaresRead)
async def update_billing_software(billing_software_id: int, billing_software: Billing_softwaresUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Billing_software).filter(Billing_software.id == billing_software_id))
    db_billing_software = result.scalars().first()
    if db_billing_software is None:
        raise HTTPException(status_code=404, detail="billing_software not found")
    for var, value in vars(billing_software).items():
        setattr(db_billing_software, var, value) if value is not None else None
    await db.commit()
    await db.refresh(db_billing_software)
    return db_billing_software

@router.delete("/{billing_software_id}", response_model=Billing_softwaresRead)
async def delete_billing_software(billing_software_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Billing_software).filter(Billing_software.id == billing_software_id))
    billing_software = result.scalars().first()
    if billing_software is None:
        raise HTTPException(status_code=404, detail="billing_software not found")
    await db.delete(billing_software)
    await db.commit()
    return billing_software
