from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.orders import Order
from app.schemas.orders import OrderRead
# from app.models.product import Product
# from app.models.shipment import Shipment 
# from app.schemas.shipment import ShipmentCreate, ShipmentRead, ShipmentUpdate
from app.models.awb import AWB
from app.schemas.awb import AWBCreate, AWBRead
from app.utils.awb import generate_awb_number
from app.database import get_db
from sqlalchemy import func, any_
import datetime
from decimal import Decimal

router = APIRouter()

@router.get('/orders')
async def get_orders_info(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.status == any_([1,2,3])))
    orders = result.scalars().all()
    return {
        "orders": orders
    }

@router.post("/awb", response_model=AWBRead)
async def generate_awb(awb_create: AWBCreate, db: AsyncSession = Depends(get_db)):
    return await create_awb(db, awb_create)

async def create_awb(db: AsyncSession, awb_create: AWBCreate):
    result = await db.execute(select(Order).where(Order.id == awb_create.order_id))
    order = result.scalars().first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    awb_number = generate_awb_number()
    db_awb = AWB(
        awb_number=awb_number,
        order_id=awb_create.order_id,
        observation_field=awb_create.observation_field
    )
    db.add(db_awb)
    await db.commit()
    await db.refresh(db_awb)
    return db_awb