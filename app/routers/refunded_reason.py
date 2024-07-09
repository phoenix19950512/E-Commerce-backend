from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.refunded_reason import RefundedReason
from app.schemas.refunded_reason import RefundedReasonCreate, RefundedReasonRead, RefundedReasonUpdate

router = APIRouter()

@router.post("/", response_model=RefundedReasonRead)
async def create_refunded_reason(refunded_reason: RefundedReasonCreate, db: AsyncSession = Depends(get_db)):
    db_refunded_reason = RefundedReason(**refunded_reason.dict())
    db.add(db_refunded_reason)
    await db.commit()
    await db.refresh(db_refunded_reason)
    return db_refunded_reason

@router.get('/count')
async def get_refunded_reasons_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(func.count(RefundedReason.id))
    count = result.scalar()
    return count

@router.get("/", response_model=List[RefundedReasonRead])
async def get_refunded_reasons(
    page: int = Query(1, ge=1, description="Page number"),
    items_per_page: int = Query(50, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_db)
):
    
    offset = (page - 1) * items_per_page
    result = await db.execute(select(RefundedReason).offset(offset).limit(items_per_page))
    db_refunded_reasons = result.scalars().all()
    if db_refunded_reasons is None:
        raise HTTPException(status_code=404, detail="refunded_reason not found")
    return db_refunded_reasons

@router.put("/{refunded_reason_id}", response_model=RefundedReasonRead)
async def update_refunded_reason(refunded_reason_id: int, refunded_reason: RefundedReasonUpdate, db: AsyncSession = Depends(get_db)):
    db_refunded_reason = await db.execute(select(RefundedReason).filter(RefundedReason.id == refunded_reason_id)).scalars().first()
    if db_refunded_reason is None:
        raise HTTPException(status_code=404, detail="refunded_reason not found")
    for var, value in vars(RefundedReason).items():
        setattr(db_refunded_reason, var, value) if value else None
    await db.commit()
    await db.refresh(db_refunded_reason)
    return db_refunded_reason

@router.delete("/{refunded_reason_id}", response_model=RefundedReasonRead)
async def delete_refunded_reason(refunded_reason_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RefundedReason).filter(RefundedReason.id == refunded_reason_id))
    refunded_reason = result.scalars().first()
    if refunded_reason is None:
        raise HTTPException(status_code=404, detail="refunded_reason not found")
    await db.delete(refunded_reason)
    await db.commit()
    return refunded_reason
