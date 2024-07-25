from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy.sql import text
from sqlalchemy import func
from typing import List
from app.schemas.orders import OrderCreate, OrderUpdate, OrderRead
from app.models.orders import Order
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.config import settings

async def get_order(db: AsyncSession, order_id: int):
    result = await db.execute(select(Order).filter(Order.id == order_id))
    return result.scalars().first()

def get_orders(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Order).offset(skip).limit(limit).all()

async def update_order(db: Session, order_id: int, order: OrderUpdate):
    result = await db.execute(select(Order).filter(Order.id == order_id))
    db_order = result.scalars().first()
    if db_order:
        for key, value in order.dict().items():
            setattr(db_order, key, value)
        db.commit()
        db.refresh(db_order)
    return db_order

async def delete_order(db: Session, order_id: int):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if db_order:
        db.delete(db_order)
        db.commit()
    return db_order

router = APIRouter()

@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate, db: AsyncSession = Depends(get_db)):
    db_order = Order(**order.dict())
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)
    return db_order

@router.get("/", response_model=List[OrderRead])
async def read_orders(
    flag: bool = Query(1),
    page: int = Query(1, ge=1, description="Page number"),
    items_per_page: int = Query(50, ge=1, le=100, description="Number of items per page"),
    status: int = Query(-1, description="Status of the order"),
    search_text: str = Query('', description="Text for searching"),
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * items_per_page
    if status == -1:
        query = select(Order).filter(
            (Order.vendor_name.ilike(f"%{search_text}%")) |
            (Order.payment_mode.ilike(f"%{search_text}%")) |
            (Order.details.ilike(f"%{search_text}%")) |
            (Order.order_market_place.ilike(f"%{search_text}%")) |
            (Order.delivery_mode.ilike(f"%{search_text}%")) |
            (Order.proforms.ilike(f"%{search_text}%"))
        ).offset(offset).limit(items_per_page)
    else :
        query = select(Order).where(Order.status == status).filter(
            (Order.vendor_name.ilike(f"%{search_text}%")) |
            (Order.payment_mode.ilike(f"%{search_text}%")) |
            (Order.details.ilike(f"%{search_text}%")) |
            (Order.order_market_place.ilike(f"%{search_text}%")) |
            (Order.delivery_mode.ilike(f"%{search_text}%")) |
            (Order.proforms.ilike(f"%{search_text}%"))
        ).offset(offset).limit(items_per_page)

    if flag == True:
        query = query.order_by(Order.date.desc())
    else:
        query = query.order_by(Order.date.asc())
    
    result = await db.execute(query)
    db_orders = result.scalars().all()
    
    if db_orders is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_orders

@router.get('/count')
async def get_orders_count(
    status: int = Query(-1, description="Status of the order"),
    search_text: str = Query('', description="Text for searching"),
    db: AsyncSession = Depends(get_db)
):
    if status == -1:
        result = await db.execute(select(func.count()).select_from(Order).filter(
            (Order.vendor_name.ilike(f"%{search_text}%")) |
            (Order.payment_mode.ilike(f"%{search_text}%")) |
            (Order.details.ilike(f"%{search_text}%")) |
            (Order.order_market_place.ilike(f"%{search_text}%")) |
            (Order.delivery_mode.ilike(f"%{search_text}%")) |
            (Order.proforms.ilike(f"%{search_text}%"))
        ))
    else:
        result = await db.execute(select(func.count()).select_from(Order).where(Order.status == status).filter(
            (Order.vendor_name.ilike(f"%{search_text}%")) |
            (Order.payment_mode.ilike(f"%{search_text}%")) |
            (Order.details.ilike(f"%{search_text}%")) |
            (Order.order_market_place.ilike(f"%{search_text}%")) |
            (Order.delivery_mode.ilike(f"%{search_text}%")) |
            (Order.proforms.ilike(f"%{search_text}%"))
        ))
    count = result.scalar()
    return count


@router.get("/{order_id}", response_model=OrderRead)
async def read_order(order_id: int, db: Session = Depends(get_db)):
    db_order = await get_order(db=db, order_id=order_id)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order

@router.put("/{order_id}", response_model=OrderRead)
async def get_update_order(order_id: int, order: OrderUpdate, db: Session = Depends(get_db)):
    db_order = await update_order(db=db, order_id=order_id, order=order)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order

@router.delete("/{order_id}", response_model=OrderRead)
async def get_delete_order(order_id: int, db: Session = Depends(get_db)):
    db_order = await delete_order(db=db, order_id=order_id)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order
