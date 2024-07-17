from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.refunded import Refunded
from app.schemas.refunded import RefundedCreate, RefundedRead, RefundedUpdate

router = APIRouter()

@router.post("/", response_model=RefundedRead)
async def create_refunded_(refunded: RefundedCreate, db: AsyncSession = Depends(get_db)):
    db_refunded = Refunded(**refunded.dict())
    db.add(db_refunded)
    await db.commit()
    await db.refresh(db_refunded)
    return db_refunded

@router.get('/count')
async def get_refunded_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(func.count(Refunded.order_id))
    count = result.scalar()
    return count

@router.get("/", response_model=List[RefundedRead])
async def get_refunded_s(
    page: int = Query(1, ge=1, description="Page number"),
    items_per_page: int = Query(50, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_db)
):
    
    offset = (page - 1) * items_per_page
    result = await db.execute(select(Refunded).offset(offset).limit(items_per_page))
    db_refundeds = result.scalars().all()
    if db_refundeds is None:
        raise HTTPException(status_code=404, detail="refunded not found")
    return db_refundeds

@router.put("/{refunded_id}", response_model=RefundedRead)
async def update_refunded(refunded_id: int, refunded: RefundedUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Refunded).filter(Refunded.order_id == refunded_id))
    db_refunded = result.scalars().first()
    if db_refunded is None:
        raise HTTPException(status_code=404, detail="refunded not found")
    for var, value in vars(refunded).items():
        setattr(db_refunded, var, value) if value else None
    await db.commit()
    await db.refresh(db_refunded)
    return db_refunded

@router.delete("/{refunded__id}", response_model=RefundedRead)
async def delete_refunded(refunded_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Refunded).filter(Refunded.order_id == refunded_id))
    refunded = result.scalars().first()
    if refunded is None:
        raise HTTPException(status_code=404, detail="refunded not found")
    await db.delete(refunded)
    await db.commit()
    return refunded
