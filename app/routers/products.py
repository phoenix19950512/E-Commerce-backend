from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.orders import Order
from app.schemas.orders import OrderRead
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.models.shipment import Shipment
from app.models.marketplace import Marketplace
import json

import datetime
import base64

router = APIRouter()

@router.post("/", response_model=ProductRead)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    db_product = Product(**product.dict())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product

# @router.post("/", response_model=ProductRead)
# async def create_product(product: ProductCreate, marketplace_id: int, db: AsyncSession = Depends(get_db)):
#     db_product = Product(**product.dict())
    
#     result = await db.execute(select(Marketplace).filter(Marketplace.id == marketplace_id))
#     marketplace = result.scalars().first()
#     if not marketplace:
#         raise HTTPException(status_code=404, detail="Marketplace not found")
#     MARKETPLACE_API_URL = marketplace.baseAPIURL
#     USERNAME = marketplace.credentials["firstKey"]
#     PASSWORD = marketplace.credentials["secondKey"]
#     API_KEY = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode('utf-8'))
#     try:
#         emag_response = create_product(MARKETPLACE_API_URL, API_KEY, db_product, PUBLIC_KEY=None, usePublicKey=False)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))    
#     return db_product

@router.get('/count')
async def get_products_count(db: AsyncSession = Depends(get_db)):
    print(dir(db))
    result = await db.execute(func.count(Product.id))
    count = result.scalar()
    return count

@router.get("/{product_id}", response_model=ProductRead)
async def read_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).filter(Product.id == product_id))
    product = result.scalars().first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/sales_info/{product_id}")
async def get_sales_info(
    product_id: int,
    type: int,
    db: AsyncSession = Depends(get_db)      
):
    today = datetime.date.today()
    sales_info = []

    if type == 1:
        for i in range(13):
            if today.month + i <= 12:
                date = datetime.date(today.year - 1, today.month + i, today.day)
            else:
                date = datetime.date(today.year, today.month + i - 12, today.day)
            
            date_string = f"{date.strftime('%b')} {date.year}"
            st_date = datetime.date(date.year, date.month, 1)
            if date.month == 12:
                en_date = datetime.date(date.year, 12, 31)
            else:
                en_date = datetime.date(date.year, date.month + 1, 1) - datetime.timedelta(days = 1)

            st_datetime = datetime.datetime.combine(st_date, datetime.time.min)
            en_datetime = datetime.datetime.combine(en_date, datetime.time.max)
            
            sales_month_data = await get_info(product_id, st_datetime, en_datetime, db)
            sales_info.append({"date_string": date_string, "sales": sales_month_data["sales"]})

    elif type == 2:
        week_num_en = today.isocalendar()[1]
        en_date = today
        st_date = today - datetime.timedelta(today.weekday())
        for i in range(14):
            if week_num_en - i > 0:
                week_string = f"week {week_num_en - i}"
            else:
                week_string = f"week {week_num_en + 52 - i}"
            st_datetime = datetime.datetime.combine(st_date, datetime.time.min)
            en_datetime = datetime.datetime.combine(en_date, datetime.time.max)

            sales_week_data = await get_info(product_id, st_datetime, en_datetime, db)
            sales_info.append({"date_string": week_string, "sales": sales_week_data["sales"]})
            en_date = st_date - datetime.timedelta(days=1)
            st_date = st_date - datetime.timedelta(days=7)
    else:
        for i in range(30):
            date = today - datetime.timedelta(days=i)
            st_datetime = datetime.datetime.combine(date, datetime.time.min)
            en_datetime = datetime.datetime.combine(date, datetime.time.max)

            day_string = f"{date.day} {date.strftime('%b')} {date.year}"
            sales_day_info = await get_info(product_id, st_datetime, en_datetime, db)
            sales_info.append({"date_string": day_string, "sales": sales_day_info["sales"]})

    return sales_info

async def get_info(product_id: int, st_datetime, en_datetime, db: AsyncSession):
    query = select(Order).where(Order.date >= st_datetime, Order.date <= en_datetime)
    query = query.where(Order.product_id == product_id)
    result = await db.execute(query)
    orders = result.scalars().all()

    units = len(orders)
    return {
        "sales": units
    }

@router.get("/orders_info/{product_id}")
async def get_orders_info(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).filter(Order.product_id == product_id))
    db_order = result.scalars().all()

    order_data = [
        {
            "order_id": order.id,
            "order_date": order.date,
            "customer_name": "customer_name",
            "quantity_orders": order.unit,
            "order_status": order.status
        } for order in db_order
    ]
    return order_data
    
@router.get("/refunded_info/{products_id}")    
async def get_refunded_info(products_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Order.refunded_reason_id, func.count(Order.id))
        .filter(Order.product_id == products_id)
        .group_by(Order.refunded_reason_id)
    )
    refunded_info = result.all()

    # Transform the result into a dictionary or another suitable format
    refunded_info_list = [
        {"refunded_reason_id": refunded_reason_id, "refunded_number": refunded_number} for refunded_reason_id, refunded_number in refunded_info
    ]
    return refunded_info_list

@router.get("/shipment_info/{product_id}")
async def get_shipment_info(
    product_id: int, 
    db: AsyncSession = Depends(get_db)
):
    select_product = await db.execute(select(Product).filter(Product.id == product_id))
    product = select_product.scalars().first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product_name = product.product_name

    result = await db.execute(select(Shipment))
    shipments = result.scalars().all()

    if not shipments:
        raise HTTPException(status_code=404, detail="Shipments not found")
    
    shipment_data = []
    for shipment in shipments:
        try:
            product_name_list = json.loads(shipment.product_name_list)
        except (TypeError, json.JSONDecodeError):
            continue

        if product_name in product_name_list:
            index = shipment.product_name_list.index(product_name)
            shipment_quantity = shipment.quantity_list[index]
            quantity_sum = sum(shipment.quantity_list)

        shipment_data.append({
            "shipment_id": shipment.id,
            "shipment_date": shipment.date,
            "shipment_quantity": quantity_sum,
            "supplier_name": shipment.supplier_name,
            "shipment_status": shipment.status,
            "shipment_product_quantity": shipment_quantity
        })

    return shipment_data

@router.get("/", response_model=List[ProductRead])
async def get_products(
    supplier_ids: str = Query(None),
    page: int = Query(1, ge=1, description="Page number"),
    items_per_page: int = Query(50, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_db)
):
    
    offset = (page - 1) * items_per_page
    if supplier_ids:
        supplier_id_list = [int(id.strip()) for id  in supplier_ids.split(",")]
        result = await db.execute(select(Product).filter(Product.supplier_id.in_(supplier_id_list)).offset(offset).limit(items_per_page))
    else:
        result = await db.execute(select(Product).offset(offset).limit(items_per_page))
    db_products = result.scalars().all()
    if db_products is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_products

@router.put("/{product_id}", response_model=ProductRead)
async def update_product(product_id: int, product: ProductUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).filter(Product.id == product_id))
    db_product = result.scalars().first()

    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for var, value in vars(product).items():
        if value is not None:
            setattr(db_product, var, value)

    await db.commit()
    await db.refresh(db_product)
    return db_product

@router.delete("/{product_id}", response_model=ProductRead)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).filter(Product.id == product_id))
    product = result.scalars().first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    await db.delete(product)
    await db.commit()
    return product
