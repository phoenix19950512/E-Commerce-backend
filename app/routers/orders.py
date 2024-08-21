from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy.sql import text
from sqlalchemy import func
from typing import List
from app.schemas.orders import OrderCreate, OrderUpdate, OrderRead
from app.models.orders import Order
from app.models.product import Product
from app.models.internal_product import Internal_Product
from app.models.marketplace import Marketplace
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.config import settings
from sqlalchemy import any_
from sqlalchemy import cast, String
from decimal import Decimal
import json

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

@router.get("/new_order")
async def read_new_orders(
    flag: bool = Query(1),
    search_text: str = Query('', description="Text for searching"),
    warehouse_id: int = Query('', description='warehouse_id'),
    db: AsyncSession = Depends(get_db)
):
    query = select(Order).filter(
        (cast(Order.id, String).ilike(f"%{search_text}%")) |
        (Order.payment_mode.ilike(f"%{search_text}%")) |
        (Order.details.ilike(f"%{search_text}%")) |
        (Order.order_market_place.ilike(f"%{search_text}%")) |
        (Order.delivery_mode.ilike(f"%{search_text}%")) |
        (Order.proforms.ilike(f"%{search_text}%"))
    )
    query = query.filter(Order.status == any_([1, 2, 3]))

    if flag == True:
        query = query.order_by(Order.date.desc())
    else:
        query = query.order_by(Order.date.asc())

    result = await db.execute(query)
    db_new_orders = result.scalars().all()
    new_order_data = []
    for db_order in db_new_orders:
        image_link = []
        stock = []
        marketplace = db_order.order_market_place
        product_list = db_order.product_id
        quantity_list = db_order.quantity
        sale_price = db_order.sale_price
        total = Decimal(0)
        result = await db.execute(select(Marketplace).where(Marketplace.marketplaceDomain == marketplace))
        db_marketplace = result.scalars().first()
        vat = db_marketplace.vat

        flag = 1
        for i in range(len(product_list)):
            product_id = product_list[i]
            result = await db.execute(select(Product).where(Product.id == product_id))
            db_product = result.scalars().first()

            ean = db_product.ean
            
            result = await db.execute(select(Internal_Product).where(Internal_Product.ean == ean))
            db_internal_product = result.scalars().first()

            if db_internal_product.warehouse_id != warehouse_id:
                flag = 0
                break

        if flag == 0:
            continue

        for i in range(len(product_list)):
            quantity = quantity_list[i]
            price = sale_price[i]
            if marketplace.lower() == 'emag.ro' or marketplace.lower() == 'emag.bg':
                real_price = round(Decimal(price) * (100 + vat) / 100, 2)
            elif marketplace.lower() == 'emag.hu':
                real_price = round(Decimal(price) * (100 + vat) / 100, 0)
            else:
                real_price = round(Decimal(price) * (100 + vat) / 100, 4)
            total += real_price * quantity

        if db_order.shipping_tax:
            total += Decimal(db_order.shipping_tax)
        if db_order.vouchers:
            vouchers = json.loads(db_order.vouchers) if isinstance(db_order.vouchers, str) else db_order.vouchers
            for voucher in vouchers:
                total += Decimal(voucher.get("sale_price", "0"))
                total += Decimal(voucher.get("sale_price_vat", "0"))

        for i in range(len(product_list)):
            image_link.append("")
            product_id = product_list[i]
            result = await db.execute(select(Product).where(Product.id == product_id))
            db_products = result.scalars().all()
            for db_product in db_products:
                if db_product.product_marketplace.lower() == 'emag.ro':
                    image_link[i] = db_product.image_link
                    break
            for db_product in db_products:
                stock.append(db_product.stock)
                break
        
        
        new_order_data.append({
            "order": db_order,
            "total_price": total,
            "image_link": image_link,
            "stock": stock
        })

    return new_order_data

@router.get("/count/new_order")
async def count_new_orders(
    search_text: str = Query('', description="Text for searching"),
    db: AsyncSession = Depends(get_db)
):
    query = select(Order).filter(
        (cast(Order.id, String).ilike(f"%{search_text}%")) |
        (Order.payment_mode.ilike(f"%{search_text}%")) |
        (Order.details.ilike(f"%{search_text}%")) |
        (Order.order_market_place.ilike(f"%{search_text}%")) |
        (Order.delivery_mode.ilike(f"%{search_text}%")) |
        (Order.proforms.ilike(f"%{search_text}%"))
    )
    query = query.filter(Order.status == any_([1, 2, 3]))

    result = await db.execute(query)
    db_new_orders = result.scalars().all()
    return len(db_new_orders)

@router.get("/")
async def read_orders(
    flag: bool = Query(1),
    page: int = Query(1, ge=1, description="Page number"),
    items_per_page: int = Query(50, ge=1, le=100, description="Number of items per page"),
    status: int = Query(-1, description="Status of the order"),
    search_text: str = Query('', description="Text for searching"),
    warehouse_id: int = Query('', description="warehouse_id"),
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * items_per_page
    if status == -1:
        query = select(Order).filter(
            (cast(Order.id, String).ilike(f"%{search_text}%")) |
            (Order.payment_mode.ilike(f"%{search_text}%")) |
            (Order.details.ilike(f"%{search_text}%")) |
            (Order.order_market_place.ilike(f"%{search_text}%")) |
            (Order.delivery_mode.ilike(f"%{search_text}%")) |
            (Order.proforms.ilike(f"%{search_text}%"))
        ).offset(offset).limit(items_per_page)
    else :
        query = select(Order).where(Order.status == status).filter(
            (cast(Order.id, String).ilike(f"%{search_text}%")) |
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
    
    orders_data = []

    for db_order in db_orders:
        image_link = []
        stock = []
        marketplace = db_order.order_market_place
        product_list = db_order.product_id
        quantity_list = db_order.quantity
        sale_price = db_order.sale_price
        total = Decimal(0)
        result = await db.execute(select(Marketplace).where(Marketplace.marketplaceDomain == marketplace))
        db_marketplace = result.scalars().first()
        vat = db_marketplace.vat

        flag = 1
        for i in range(len(product_list)):
            product_id = product_list[i]
            result = await db.execute(select(Product).where(Product.id == product_id))
            db_product = result.scalars().first()

            ean = db_product.ean
            
            result = await db.execute(select(Internal_Product).where(Internal_Product.ean == ean))
            db_internal_product = result.scalars().first()

            if db_internal_product.warehouse_id != warehouse_id:
                flag = 0
                break

        if flag == 0:
            continue

        for i in range(len(product_list)):
            quantity = quantity_list[i]
            price = sale_price[i]
            if marketplace.lower() == 'emag.ro' or marketplace.lower() == 'emag.bg':
                real_price = round(Decimal(price) * (100 + vat) / 100, 2)
            elif marketplace.lower() == 'emag.hu':
                real_price = round(Decimal(price) * (100 + vat) / 100, 0)
            else:
                real_price = round(Decimal(price) * (100 + vat) / 100, 4)
            total += real_price * quantity

        if db_order.shipping_tax:
            total += Decimal(db_order.shipping_tax)
        if db_order.vouchers:
            vouchers = json.loads(db_order.vouchers) if isinstance(db_order.vouchers, str) else db_order.vouchers
            for voucher in vouchers:
                total += Decimal(voucher.get("sale_price", "0"))
                total += Decimal(voucher.get("sale_price_vat", "0"))

        for i in range(len(product_list)):
            image_link.append("")
            product_id = product_list[i]
            result = await db.execute(select(Product).where(Product.id == product_id))
            db_products = result.scalars().all()
            for db_product in db_products:
                if db_product.product_marketplace.lower() == 'emag.ro':
                    image_link[i] = db_product.image_link
                    break
            for db_product in db_products:
                stock.append(db_product.stock)
                break

        orders_data.append({
            "order": db_order,
            "total_price": total,
            "image_link": image_link,
            "stock": stock
        })
    return orders_data

@router.get('/count')
async def get_orders_count(
    status: int = Query(-1, description="Status of the order"),
    search_text: str = Query('', description="Text for searching"),
    db: AsyncSession = Depends(get_db)
):
    if status == -1:
        result = await db.execute(select(func.count()).select_from(Order).filter(
            (cast(Order.id, String).ilike(f"%{search_text}%")) |
            (Order.payment_mode.ilike(f"%{search_text}%")) |
            (Order.details.ilike(f"%{search_text}%")) |
            (Order.order_market_place.ilike(f"%{search_text}%")) |
            (Order.delivery_mode.ilike(f"%{search_text}%")) |
            (Order.proforms.ilike(f"%{search_text}%"))
        ))
    else:
        result = await db.execute(select(func.count()).select_from(Order).where(Order.status == status).filter(
            (cast(Order.id, String).ilike(f"%{search_text}%")) |
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
