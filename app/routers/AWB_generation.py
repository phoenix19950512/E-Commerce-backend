from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from typing import List
from app.database import get_db
from app.models.awb import AWB
from app.models.replacement import Replacement
from app.schemas.awb import AWBCreate, AWBRead, AWBUpdate
from app.models.marketplace import Marketplace
from app.models.orders import Order
from app.models.product import Product
from app.models.internal_product import Internal_Product
from app.models.warehouse import Warehouse
from app.utils.emag_awbs import *
from app.utils.altex_awb import save_altex_awb
from app.utils.sameday import tracking
from sqlalchemy import any_

router = APIRouter()

@router.post("/manually")
async def create_awb_manually(awb: AWBCreate, db: AsyncSession = Depends(get_db)):
    db_awb = AWB(**awb.dict())
    db.add(db_awb)
    await db.commit()
    await db.refresh(db_awb)
    return db_awb

@router.post("/")
async def create_awbs(awb: AWBCreate, marketplace: str, db: AsyncSession = Depends(get_db)):
    db_awb = AWB(**awb.dict())
    order_id = db_awb.order_id
    number = db_awb.number
    result = await db.execute(select(AWB).where(AWB.order_id == order_id, AWB.number == number))
    awb = result.scalars().first()

    if awb:
        return awb

    result = await db.execute(select(Marketplace).where(Marketplace.marketplaceDomain == marketplace))
    market_place = result.scalars().first()

    try:
        if market_place.marketplaceDomain == "altex.ro":
            data = {
                "courier_id": db_awb.courier_account_id,
                "location_id": db_awb.receiver_locality_id,
                "sender_name": db_awb.sender_name,
                "sender_contact_person": None,
                "sender_phone": db_awb.sender_phone1,
                "sender_address": db_awb.sender_street,
                "sender_country": None,
                "sender_city": None,
                "sender_postalcode": db_awb.sender_zipcode,
                "destination_contact_person ": db_awb.receiver_contact,
                "destination_phone": db_awb.receiver_phone1,
                "destination_address": db_awb.receiver_street,
                "destination_county ": None,
                "destination_postalcode ": db_awb.receiver_zipcode,
            }

            result = await save_altex_awb(market_place, data, db_awb.order_id, db)
        else:
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

            result = await save_awb(market_place, data, db)
        
        result = result.json()
        if result['isError'] == True:
            return result
        results = result['results']
        db_awb.reservation_id = results.get('reservation_id') if results.get('reservation_id') else 0
        db_awb.courier_id = results.get('courier_id') if results.get('courier_id') else 0
        db_awb.courier_name = results.get('courier_name') if results.get('courier_name') else ""
        if results.get('awb'):
            result_awb = results.get('awb')[0]
            db_awb.awb_number = result_awb.get('awb_number') if result_awb.get('awb_number') else ""
            db_awb.awb_barcode = result_awb.get('awb_barcode') if result_awb.get('awb_barcode') else ""
        db.add(db_awb)
        await db.commit()
        await db.refresh(db_awb)

        db_replacement = None

        if db_awb.number < 0:
            result = await db.execute(select(Replacement).where(Replacement.order_id == db_awb.order_id, Replacement.number == -db_awb.number))
            db_replacement = result.scalars().first()
            if db_replacement:
                db_replacement.awb = db_awb.awb_number
        
        if db_replacement:
            await db.refresh(db_replacement) 
        return db_awb
    except Exception as e:  # Roll back any changes made before the error
        logging.info(f"Error processing AWB: {str(e)}")
        return {"error": "Failed to process AWB", "message": str(e)}

@router.get("/awb_status")
async def get_awb_status(
    page: int = Query(1, ge=1, description="Page number"),
    items_per_page: int = Query(50, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * items_per_page
    result = await db.execute(select(AWB).where(AWB.awb_status > 0))
    awbs = result.scalars().all()
    number = len(awbs)

    result = await db.execute(select(AWB).where(AWB.awb_status > 0).offset(offset).limit(items_per_page))
    db_awbs = result.scalars().all()
    if db_awbs is None:
        raise HTTPException(status_code=404, detail="awbs not found")
    cnt = 1
    
    for awb in db_awbs:
        awb_number = awb.awb_number
        logging.info(f"!@##@!#@!#@#@ {cnt} awb_number is {awb_number}")
        cnt += 1
        status = await tracking(awb_number)
        logging.info(f"!@##@!#@!#@#@ Status is {status}")
        awb.awb_status = status
        
    await db.commit()
    
    return {"message": "Successfully updated AWB statuses", "total_awbs": number, "updated_records": cnt - 1}

@router.get("/count")
async def count_awb(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AWB))
    db_awb = result.scalars().all()
    return len(db_awb)

@router.get("/order_id")
async def get_awbs_order_id(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AWB).where(AWB.order_id == order_id))
    db_awbs = result.scalars().all()
    return db_awbs

@router.get("/awb_barcode")
async def get_order(
    awb_number: str,
    db: AsyncSession = Depends(get_db)
):

    if awb_number[:2] == "01":
        result = await db.execute(select(AWB).where(or_(AWB.awb_number == awb_number[2:], AWB.awb_number == awb_number[2:-3], AWB.awb_number == awb_number, AWB.awb_number == awb_number[:-3])))
    else:
        result = await db.execute(select(AWB).where(or_(AWB.awb_number == awb_number, AWB.awb_number == awb_number[:-3])))
    db_awb = result.scalars().first()
    if db_awb is None:
        raise HTTPException(status_code=404, detail="awb not found")
    order_id = db_awb.order_id
    result = await db.execute(select(Order).where(Order.id == order_id))
    db_order = result.scalars().first()
    if db_order is None:
        return HTTPException(status_code=404, detail=f"{order_id} not found")
    product_ids = db_order.product_id
    marketplace = db_order.order_market_place
    ean = []
    for product_id in product_ids:
        result = await db.execute(select(Product).where(Product.id == product_id, Product.product_marketplace == marketplace))
        product = result.scalars().first()
        if product is None:
            result = await db.execute(select(Product).where(Product.id == product_id))
            product = result.scalars().first()
        ean.append(product.ean)

    return {
        **{column.name: getattr(db_order, column.name) for column in Order.__table__.columns},
        "ean": ean
    }

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
    
    result = await db.execute(select(Internal_Product).where(Internal_Product.id == any_(db_product_list)))
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
        setattr(awb, key, value) if value is not None else None
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
