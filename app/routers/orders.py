from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm import aliased
from sqlalchemy.future import select
from sqlalchemy.sql import text
from sqlalchemy import func, distinct, exists
from typing import List
from app.schemas.orders import OrderCreate, OrderUpdate, OrderRead
from app.models.orders import Order
from app.models.product import Product
from app.models.internal_product import Internal_Product
from app.models.awb import AWB
from app.models.marketplace import Marketplace
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.config import settings
from sqlalchemy import any_, and_
from sqlalchemy import cast, String, BigInteger
from decimal import Decimal
from collections import defaultdict
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
            setattr(db_order, key, value) if value is not None else None
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
    status: int = Query(-1, description="Status of the new order"),
    db: AsyncSession = Depends(get_db)
):
    Internal_productAlias = aliased(Internal_Product)
    ProductAlias = aliased(Product)
    query = select(Order).filter(
        (cast(Order.id, String).ilike(f"%{search_text}%")) |
        (Order.payment_mode.ilike(f"%{search_text}%")) |
        (Order.details.ilike(f"%{search_text}%")) |
        (Order.order_market_place.ilike(f"%{search_text}%")) |
        (Order.delivery_mode.ilike(f"%{search_text}%")) |
        (Order.proforms.ilike(f"%{search_text}%"))
    )
    if status == -1:
        query = query.filter(Order.status == any_([1, 2, 3]))
    else:
        query = query.filter(Order.status == status)
    if flag == True:
        query = query.order_by(Order.date.desc())
    else:
        query = query.order_by(Order.date.asc())

    if warehouse_id == -1:
        query = query.join(ProductAlias, and_(ProductAlias.id == any_(Order.product_id), ProductAlias.product_marketplace == Order.order_market_place))
        query = query.join(Internal_productAlias, Internal_productAlias.ean == ProductAlias.ean)
        query = query.filter(Internal_productAlias.warehouse_id != 0)
        query = query.group_by(Order.id)  # Group by Order.id or other relevant columns
        query = query.having(func.count(distinct(Internal_productAlias.warehouse_id)) > 1)

    elif warehouse_id == -2:
        query = query.join(ProductAlias, and_(ProductAlias.id == any_(Order.product_id), ProductAlias.product_marketplace == Order.order_market_place))
        query = query.join(Internal_productAlias, Internal_productAlias.ean == ProductAlias.ean)
        query = query.filter(Internal_productAlias.warehouse_id == 0)
    elif warehouse_id and warehouse_id > 0:
        query = query.join(ProductAlias, and_(ProductAlias.id == any_(Order.product_id), ProductAlias.product_marketplace == Order.order_market_place))
        query = query.join(Internal_productAlias, Internal_productAlias.ean == ProductAlias.ean)
        query = query.group_by(Order.id)
        query = query.having(func.count(distinct(Internal_productAlias.warehouse_id)) == 1)
        query = query.having(
            and_(
                func.count(distinct(Internal_productAlias.warehouse_id)) == 1,
                func.max(Internal_productAlias.warehouse_id) == warehouse_id
            )
        )
    result = await db.execute(query)
    db_orders = result.scalars().all()
    
    if db_orders is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order_ids = [order.id for order in db_orders]

    awb_query = select(AWB).where(cast(AWB.order_id, BigInteger) == any_(order_ids))
    awb_result = await db.execute(awb_query)
    awbs = awb_result.scalars().all()

    awb_dict = defaultdict(list)
    for awb in awbs:
        awb_dict[awb.order_id].append(awb)

    orders_data = []

    for db_order in db_orders:
        ean = []
        stock = []
        marketplace = db_order.order_market_place
        product_list = db_order.product_id
        quantity_list = db_order.quantity
        sale_price = db_order.sale_price
        total = Decimal(0)
        result = await db.execute(select(Marketplace).where(Marketplace.marketplaceDomain == marketplace))
        db_marketplace = result.scalars().first()
        vat = db_marketplace.vat

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
            product_id = product_list[i]
            result = await db.execute(select(Product).where(Product.id == product_id))
            db_product = result.scalars().first()
            ean.append(db_product.ean)

        orders_data.append({
            **{column.name: getattr(db_order, column.name) for column in Order.__table__.columns},
            "total_price": total,
            "ean": ean,
            "stock": stock,
            "awb": awb_dict[db_order.id]
        })

    return orders_data

@router.get("/count/new_order")
async def count_new_orders(
    search_text: str = Query('', description="Text for searching"),
    warehouse_id: int = Query('', description="warehouse_id"),
    status: int = Query(-1, description="Status of the order"),
    db: AsyncSession = Depends(get_db)
):
    Internal_productAlias = aliased(Internal_Product)
    ProductAlias = aliased(Product)
    query = select(Order).filter(
        (cast(Order.id, String).ilike(f"%{search_text}%")) |
        (Order.payment_mode.ilike(f"%{search_text}%")) |
        (Order.details.ilike(f"%{search_text}%")) |
        (Order.order_market_place.ilike(f"%{search_text}%")) |
        (Order.delivery_mode.ilike(f"%{search_text}%")) |
        (Order.proforms.ilike(f"%{search_text}%"))
    )
    if status == -1:
        query = query.filter(Order.status == any_([1, 2, 3]))
    else:
        query = query.filter(Order.status == status)

    if warehouse_id == -1:
        query = query.join(ProductAlias, and_(ProductAlias.id == any_(Order.product_id), ProductAlias.product_marketplace == Order.order_market_place))
        query = query.join(Internal_productAlias, Internal_productAlias.ean == ProductAlias.ean)
        query = query.filter(Internal_productAlias.warehouse_id != 0)
        query = query.group_by(Order.id)  # Group by Order.id or other relevant columns
        query = query.having(func.count(distinct(Internal_productAlias.warehouse_id)) > 1)

    elif warehouse_id == -2:
        query = query.join(ProductAlias, and_(ProductAlias.id == any_(Order.product_id), ProductAlias.product_marketplace == Order.order_market_place))
        query = query.join(Internal_productAlias, Internal_productAlias.ean == ProductAlias.ean)
        query = query.filter(Internal_productAlias.warehouse_id == 0)
    elif warehouse_id and warehouse_id > 0:
        query = query.join(ProductAlias, and_(ProductAlias.id == any_(Order.product_id), ProductAlias.product_marketplace == Order.order_market_place))
        query = query.join(Internal_productAlias, Internal_productAlias.ean == ProductAlias.ean)
        query = query.group_by(Order.id)
        query = query.having(func.count(distinct(Internal_productAlias.warehouse_id)) == 1)
        query = query.having(
            and_(
                func.count(distinct(Internal_productAlias.warehouse_id)) == 1,
                func.max(Internal_productAlias.warehouse_id) == warehouse_id
            )
        )
    result = await db.execute(query)
    orders = result.scalars().all()   
    return len(orders)

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
    AWBAlias = aliased(AWB)
    Internal_productAlias = aliased(Internal_Product)
    ProductAlias = aliased(Product)
    offset = (page - 1) * items_per_page

    query = select(Order, AWBAlias).filter(
        (cast(Order.id, String).ilike(f"%{search_text}%")) |
        (Order.payment_mode.ilike(f"%{search_text}%")) |
        (Order.details.ilike(f"%{search_text}%")) |
        (Order.order_market_place.ilike(f"%{search_text}%")) |
        (Order.delivery_mode.ilike(f"%{search_text}%")) |
        (Order.proforms.ilike(f"%{search_text}%"))
    ).outerjoin(
        AWBAlias,
        AWBAlias.order_id == Order.id
    )
    
    # Apply status filter if needed 
    if status != -1:
        query = query.where(Order.status == status)

    # Sorting
    if flag:
        query = query.order_by(Order.date.desc())
    else:
        query = query.order_by(Order.date.asc())

    # Execute query

    if warehouse_id == -1:
        query = query.join(ProductAlias, and_(ProductAlias.id == any_(Order.product_id), ProductAlias.product_marketplace == Order.order_market_place))
        query = query.join(Internal_productAlias, Internal_productAlias.ean == ProductAlias.ean)
        query = query.filter(Internal_productAlias.warehouse_id != 0)
        query = query.group_by(Order.id, AWBAlias.order_id)  # Group by Order.id or other relevant columns
        query = query.having(func.count(distinct(Internal_productAlias.warehouse_id)) > 1)

    elif warehouse_id == -2:
        query = query.join(ProductAlias, and_(ProductAlias.id == any_(Order.product_id), ProductAlias.product_marketplace == Order.order_market_place))
        query = query.join(Internal_productAlias, Internal_productAlias.ean == ProductAlias.ean)
        query = query.filter(Internal_productAlias.warehouse_id == 0)
    elif warehouse_id and warehouse_id > 0:
        query = query.join(ProductAlias, and_(ProductAlias.id == any_(Order.product_id), ProductAlias.product_marketplace == Order.order_market_place))
        query = query.join(Internal_productAlias, Internal_productAlias.ean == ProductAlias.ean)
        query = query.group_by(Order.id, AWBAlias.order_id)
        query = query.having(func.count(distinct(Internal_productAlias.warehouse_id)) == 1)
        query = query.having(
            and_(
                func.count(distinct(Internal_productAlias.warehouse_id)) == 1,
                func.max(Internal_productAlias.warehouse_id) == warehouse_id
            )
        )
    query = query.offset(offset).limit(items_per_page)
    result = await db.execute(query)
    db_orders = result.all()
    
    if db_orders is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    orders_data = []

    for db_order, awb in db_orders:
        ean = []
        stock = []
        marketplace = db_order.order_market_place
        product_list = db_order.product_id
        quantity_list = db_order.quantity
        sale_price = db_order.sale_price
        total = Decimal(0)
        result = await db.execute(select(Marketplace).where(Marketplace.marketplaceDomain == marketplace))
        db_marketplace = result.scalars().first()
        vat = db_marketplace.vat

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
            product_id = product_list[i]
            result = await db.execute(select(Product).where(Product.id == product_id))
            db_product = result.scalars().first()
            ean.append(db_product.ean)

        orders_data.append({
            **{column.name: getattr(db_order, column.name) for column in Order.__table__.columns},
            "total_price": total,
            "ean": ean,
            "stock": stock,
            "awb": awb
        })

    return orders_data

@router.get('/count')
async def get_orders_count(
    status: int = Query(-1, description="Status of the order"),
    search_text: str = Query('', description="Text for searching"),
    warehouse_id: int = Query('', description="warehoues_id"),
    db: AsyncSession = Depends(get_db)
):
    Internal_productAlias = aliased(Internal_Product)
    ProductAlias = aliased(Product)

    query = select(Order).filter(
        (cast(Order.id, String).ilike(f"%{search_text}%")) |
        (Order.payment_mode.ilike(f"%{search_text}%")) |
        (Order.details.ilike(f"%{search_text}%")) |
        (Order.order_market_place.ilike(f"%{search_text}%")) |
        (Order.delivery_mode.ilike(f"%{search_text}%")) |
        (Order.proforms.ilike(f"%{search_text}%"))
    )
    
    # Apply status filter if needed 
    if status != -1:
        query = query.where(Order.status == status)

    # Execute query
    if warehouse_id == -1:
        query = query.join(ProductAlias, and_(ProductAlias.id == any_(Order.product_id), ProductAlias.product_marketplace == Order.order_market_place))
        query = query.join(Internal_productAlias, Internal_productAlias.ean == ProductAlias.ean)
        query = query.filter(Internal_productAlias.warehouse_id != 0)
        query = query.group_by(Order.id)  # Group by Order.id or other relevant columns
        query = query.having(func.count(distinct(Internal_productAlias.warehouse_id)) > 1)

    elif warehouse_id == -2:
        query = query.join(ProductAlias, and_(ProductAlias.id == any_(Order.product_id), ProductAlias.product_marketplace == Order.order_market_place))
        query = query.join(Internal_productAlias, Internal_productAlias.ean == ProductAlias.ean)
        query = query.filter(Internal_productAlias.warehouse_id == 0)
    elif warehouse_id and warehouse_id > 0:
        query = query.join(ProductAlias, and_(ProductAlias.id == any_(Order.product_id), ProductAlias.product_marketplace == Order.order_market_place))
        query = query.join(Internal_productAlias, Internal_productAlias.ean == ProductAlias.ean)
        query = query.group_by(Order.id)
        query = query.having(func.count(distinct(Internal_productAlias.warehouse_id)) == 1)
        query = query.having(
            and_(
                func.count(distinct(Internal_productAlias.warehouse_id)) == 1,
                func.max(Internal_productAlias.warehouse_id) == warehouse_id
            )
        )
    result = await db.execute(query)
    orders = result.scalars().all()   
    return len(orders)

@router.get("/{order_id}")
async def read_order(order_id: int, db: AsyncSession = Depends(get_db)):
    AWBAlias = aliased(AWB)
    query = select(Order, AWBAlias).outerjoin(
        AWBAlias,
        AWBAlias.order_id == Order.id
    )
    query = query.where(Order.id == order_id)
    result = await db.execute(query)

    db_order_awb = result.all()
    if db_order_awb is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    db_order, awb = db_order_awb[0]
    product_id_list = db_order.product_id
    ean = []
    stock = []
    marketplace = db_order.order_market_place
    product_list = db_order.product_id
    quantity_list = db_order.quantity
    sale_price = db_order.sale_price
    total = Decimal(0)
    result = await db.execute(select(Marketplace).where(Marketplace.marketplaceDomain == marketplace))
    db_marketplace = result.scalars().first()
    vat = db_marketplace.vat

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

    for i in range(len(product_id_list)):
        product_id = product_id_list[i]
        result = await db.execute(select(Product).where(Product.id == product_id))
        db_product = result.scalars().first()
        ean.append(db_product.ean)

    return {
        **{column.name: getattr(db_order, column.name) for column in Order.__table__.columns},
        "total_price": total,
        "ean": ean,
        "stock": stock,
        "awb": awb
    }

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
