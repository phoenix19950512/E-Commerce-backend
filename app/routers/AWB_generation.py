from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.awb import AWB
from app.schemas.awb import AWBCreate, AWBRead, AWBUpdate
from app.models.marketplace import Marketplace
from app.utils.emag_awbs import *

router = APIRouter()

@router.post("/${marketplace}", response_model=AWBRead)
async def create_awbs_(awb: AWBCreate, marketplace: str, db: AsyncSession = Depends(get_db)):
    db_awb = AWB(**awb.dict())
    db.add(db_awb)
    await db.commit()
    await db.refresh(db_awb)
    data = {
        "order_id": db_awb.order_id,
        "rma_id": db_awb.rma_id,
        "sender": {
            "name": db_awb.sender_name,
            "phone1": db_awb.sender_phone1,
            "phone2": db_awb.sender_phone2,
            "locality_id": db_awb.sender_locality_id,
            "street": db_awb.sender_street,
            "zipcode": db_awb.sender_zipcode
        },
        "receiver": {
            "name": db_awb.receiver_name,
            "phone1": db_awb.receiver_phone1,
            "phone2": db_awb.receiver_phone1,
            "locality_id": db_awb.receiver_locality_id,
            "street": db_awb.receiver_street,
            "zipcode": db_awb.receiver_street
        },
        "locker_id": db_awb.locker_id,
        "is_oversize": db_awb.is_oversize,
        "insured_vale": db_awb.insured_vale,
        "weight": db_awb.weight,
        "envelope_number": db_awb.envelope_number,
        "parcel_number": db_awb.parcel_number,
        "observation": db_awb.observation,
        "cod": db_awb.cod,
        "courier_account_id": db_awb.courier_account_id,
        "pickup_and_return": db_awb.pickup_and_return,
        "saturday_delivery": db_awb.saturday_delivery,
        "sameday_delivery": db_awb.sameday_delivery,
        "dropoff_locker": db_awb.dropoff_locker
    }

    result = await db.execute(select(Marketplace).where(Marketplace.marketplaceDomain == marketplace))
    market_place = result.scalars().first()

    result = await save_awb(market_place, data, db)
    return result

@router.get("/", response_model=List[AWBRead])
async def get_awbs(
    page: int = Query(1, ge=1, description="Page number"),
    items_per_page: int = Query(50, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_db)
):
    
    offset = (page - 1) * items_per_page
    result = await db.execute(select(AWB).offset(offset).limit(items_per_page))
    db_awbs = result.scalars().all()
    if db_awbs is None:
        raise HTTPException(status_code=404, detail="awbs not found")
    return db_awbs

@router.put("/{awb_id}", response_model=AWBRead)
async def update_awbs(awb_id: int, awb: AWBUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AWB).filter(AWB.id == awb_id))
    db_awb = result.scalars().first()
    if db_awb is None:
        raise HTTPException(status_code=404, detail="awbs not found")
    for var, value in vars(awb).items():
        setattr(db_awb, var, value) if value else None
    await db.commit()
    await db.refresh(db_awb)
    return db_awb

@router.delete("/{awbs__id}", response_model=AWBRead)
async def delete_awbs(awbs_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AWB).filter(AWB.id == awbs_id))
    awb = result.scalars().first()
    if awb is None:
        raise HTTPException(status_code=404, detail="awbs not found")
    await db.delete(awb)
    await db.commit()
    return awb
