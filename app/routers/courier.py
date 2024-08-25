from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.courier import Courier
from app.schemas.courier import CouriersCreate, CouriersRead, CouriersUpdate

router = APIRouter()

@router.post("/", response_model=CouriersRead)
async def create_couriers_(couriers: CouriersCreate, db: AsyncSession = Depends(get_db)):
    db_courier = Courier(**couriers.dict())
    db.add(db_courier)
    await db.commit()
    db.refresh(db_courier)
    return db_courier

@router.get('/count')
async def get_couriers_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(func.count(Courier.order_id))
    count = result.scalar()
    return count

@router.get("/", response_model=List[CouriersRead])
async def get_couriers(
    page: int = Query(1, ge=1, description="Page number"),
    items_per_page: int = Query(50, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_db)
):
    
    offset = (page - 1) * items_per_page
    result = await db.execute(select(Courier).offset(offset).limit(items_per_page))
    db_couriers = result.scalars().all()
    if db_couriers is None:
        raise HTTPException(status_code=404, detail="couriers not found")
    return db_couriers

@router.put("/{courier_id}", response_model=CouriersRead)
async def update_couriers(courier_id: int, courier: CouriersUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Courier).filter(Courier.id == courier_id))
    db_courier = result.scalars().first()
    if db_courier is None:
        raise HTTPException(status_code=404, detail="couriers not found")
    for var, value in vars(courier).items():
        setattr(db_courier, var, value) if value else None
    await db.commit()
    db.refresh(db_courier)
    return db_courier

@router.delete("/{couriers_id}", response_model=CouriersRead)
async def delete_couriers(courier_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Courier).filter(Courier.id == courier_id))
    couriers = result.scalars().first()
    if couriers is None:
        raise HTTPException(status_code=404, detail="couriers not found")
    await db.delete(couriers)
    await db.commit()
    return couriers
