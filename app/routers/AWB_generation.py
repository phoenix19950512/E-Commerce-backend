from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.awb import AWB
from app.schemas.awb import AWBCreate, AWBRead, AWBUpdate
from app.models.marketplace import Marketplace
from app.models.orders import Order
from app.models.product import Product
from app.models.customer import Customers
from app.models.warehouse import Warehouse
from app.utils.emag_awbs import *
from sqlalchemy import any_

router = APIRouter()

@router.post("/")
async def create_awbs_(awb: AWBCreate, marketplace: str, db: AsyncSession = Depends(get_db)):
    db_awb = AWB(**awb.dict())
    # db.add(db_awb)
    # await db.commit()
    # await db.refresh(db_awb)
    data = {
        "order_id": db_awb.order_id,
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
            "contact": db_awb.receiver_contact,
            "phone1": db_awb.receiver_phone1,
            "phone2": db_awb.receiver_phone1,
            "legal_entity": db_awb.receiver_legal_entity,
            "locality_id": db_awb.receiver_locality_id,
            "street": db_awb.receiver_street,
            "zipcode": db_awb.receiver_zipcode
        },
        "locker_id": db_awb.locker_id,
        "is_oversize": db_awb.is_oversize,
        "insured_value": db_awb.insured_value,
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

    logging.info(data)

    result = await db.execute(select(Marketplace).where(Marketplace.marketplaceDomain == marketplace))
    market_place = result.scalars().first()

    result = await save_awb(market_place, data, db)
    return result

@router.get("/customer")
async def get_customer(
    order_id: int,
    db:AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    db_order = result.scalars().first()
    customer_id = db_order.customer_id
    result = await db.execute(select(Customers).where(Customers.id == customer_id))
    db_customer = result.scalars().first()
    return db_customer

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

@router.get("/warehouse")
async def get_warehouse(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    db_order = result.scalars().first()
    db_product_list = db_order.product_id
    
    result = await db.execute(select(Product).where(Product.id == any_(db_product_list)))
    db_products = result.scalars().all()

    warehouse_id_list = []

    for product in db_products:
        warehouse_id_list.append(product.warehouse_id)

    result = await db.execute(select(Warehouse).where(Warehouse.id == any_(warehouse_id_list)))
    db_warehouses = result.scalars().all()

    return db_warehouses

@router.put("/{awb_id}", response_model=AWBRead)
async def update_awbs(awb_id: int, awb: AWBUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AWB).filter(AWB.id == awb_id))
    db_awb = result.scalars().first()
    if db_awb is None:
        raise HTTPException(status_code=404, detail="awbs not found")
    update_data = awb.dict(exclude_unset=True)  # Only update fields that are set
    for key, value in update_data.items():
        setattr(awb, key, value)
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
