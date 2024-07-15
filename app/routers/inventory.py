from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.product import Product
from app.models.shipment import Shipment 
from app.schemas.shipment import ShipmentCreate, ShipmentRead, ShipmentUpdate
from app.database import get_db
from app.utils.emag_products import *
from sqlalchemy import func, and_, text
import datetime
from decimal import Decimal

router = APIRouter()

@router.get('/product')
async def get_product_info(
    db: AsyncSession = Depends(get_db)
):
    product_result = await db.execute(select(Product))
    products = product_result.scalars().all()

    product_data = []

    if product_result:
        for product in products:
            stock = product.stock
            product_name = product.product_name

            shipment_result = await db.execute(select(Shipment))
            
            shipments = shipment_result.scalars().all()
            
            product_shipments = []

            for shipment in shipments:
                try:
                    product_name_list = json.loads(shipment.product_name_list)
                except (TypeError, json.JSONDecodeError):
                    continue
                
                if product_name in product_name_list:
                    product_shipments.append(shipment)

            if  product_shipments:
                min_date = min(shipment.date for shipment in product_shipments)
                max_date = max(shipment.date for shipment in product_shipments)

                days = (max_date - min_date).days + 1

                total_sales_number = 0
                for shipment in product_shipments:
                    if product_name in shipment.product_name_list:
                        index = shipment.product_name_list.index(product_name)
                        total_sales_number += shipment.quantity_list[index]
                    
                ave_sales = total_sales_number / days

                stock_days = int(stock / ave_sales) if ave_sales > 0 else 0
            else:
                stock_days = product.stock
            product_data.append({
                "product_name": product.product_name,
                "price": str(product.price),
                "ean": product.ean,
                "image_link": product.image_link,
                "stock": product.stock,
                "day_stock": stock_days
            })
        return product_data

@router.get('/product/advance')
async def get_product_advanced_info(
    db: AsyncSession = Depends(get_db),
    shipment_type: str = Query(None),
    weight_min: Decimal = Query(None),
    weight_max: Decimal = Query(None),
    volumetric_weight_min: Decimal = Query(None),
    volumetric_weight_max: Decimal = Query(None)
):
    query_ship = select(Shipment)

    if shipment_type is not None:
        query_ship = query_ship.where(Shipment.type == shipment_type)
    
    shipments_result = await db.execute(query_ship)
    shipments = shipments_result.scalars().all()

    product_type_list = []
    unique_names = set()

    for shipment in shipments:
        name_list = shipment.product_name_list
        for name in name_list:
            if name not in unique_names:
                product_type_list.append(name)
                unique_names.add(name)

    query = select(Product)
    if weight_min is not None:
        query = query.where(Product.weight >= weight_min)
    
    if weight_max is not None:
        query = query.where(Product.weight <= weight_max)
    
    if volumetric_weight_min is not None:
        query = query.where(Product.volumetric_weight >= volumetric_weight_min)
    
    if volumetric_weight_max is not None:
        query = query.where(Product.volumetric_weight <= volumetric_weight_max)
    
    if shipment_type is not None:
        query = query.where(Product.product_name in product_type_list)

    result = await db.execute(query)
    products = result.scalars().all()
    product_data = []

    for product in products:
        product_data.append({
            "product_name" : product.product_name,
            "price": product.price,
            "image_link": product.image_link,
            "weight": product.weight,
            "volumetric_weight": product.volumetric_weight,
            "stock": product.stock,
            "shipment_type": shipment_type
        })

    return product_data

# @router.get('/count')
# async def get_count():
#     count = count_all_products(MARKETPLACE_API_URL, PRODUCTS_ENDPOINT, COUNT_ENGPOINT, API_KEY, PUBLIC_KEY=None, usePublicKey=False, PROXIES=None)
#     return

@router.get('/shipment')
async def  get_shipment_info(
    db: AsyncSession = Depends(get_db),
    type_str: str = Query(None),
    status_str: str = Query(None)
):
    if type_str:
        type = [str(id.strip()) for id in type_str.split(",")]
    else:
        type = []

    if status_str:
        status = [str(id.strip()) for id in status_str.split(",")]
    else:
        status = []

    query = select(Shipment).where(Shipment.type.in_(type))
    query = query.where(Shipment.status.in_(status))

    result = await db.execute(query)
    shipments = result.scalars().all()

    shipment_data = []
    for shipment in shipments:
        shipment_data.append({
            "id": shipment.id,
            "date": shipment.date,
            "type": shipment.type,
            "satus": shipment.status,
            "product_list": shipment.product_name_list
        })

    return shipment_data

@router.post('/shipment')
async def create_shipment(shipment: ShipmentCreate, db: AsyncSession = Depends(get_db)):
    db_shipment = Shipment(**shipment.dict())
    db.add(db_shipment)
    await db.commit()
    await db.refresh(db_shipment)
    return db_shipment

@router.put("/shipment", response_model=ShipmentRead)
async def update_shipment(shipment_id: int, shipment: ShipmentUpdate, db: AsyncSession = Depends(get_db)):
    db_shipment = await db.execute(select(Shipment).filter(Shipment.id == shipment_id)).scalars().first()
    if db_shipment is None:
        raise HTTPException(status_code=404, detail="shipment not found")
    for var, value in vars(shipment).items():
        setattr(db_shipment, var, value) if value else None
    await db.commit()
    await db.refresh(db_shipment)
    return db_shipment

