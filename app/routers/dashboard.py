from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text, and_, func, literal_column, cast, ARRAY, Integer, BigInteger
from sqlalchemy.orm import aliased
from sqlalchemy.orm import joinedload
from app.models.product import Product
from app.schemas.product import ProductRead
from app.models.orders import Order
from app.schemas.orders import OrderRead
from app.models.refunded import Refunded
from app.schemas.refunded import RefundedRead
from typing import List, Optional
from app.database import get_db
import datetime
import asyncpg
from app.config import settings
from psycopg2.extras import RealDictCursor

async def get_db_connection():
    return await asyncpg.connect(
        database=settings.DB_NAME,
        user=settings.DB_USERNAME,
        password=settings.DB_PASSOWRD,
        host=settings.DB_URL,
        port=settings.DB_PORT,
    )

router = APIRouter()
# @router.post("/", response_model=ProductRead)

async def get_return(st_datetime, en_datetime, db:AsyncSession):
    query = select(Refunded).where(Refunded.return_type == 3)
    query = query.where(Refunded.date >= st_datetime, Refunded.date <= en_datetime)
    refunds_result = await db.execute(query)
    refunds = refunds_result.scalars().all()
    
    return len(refunds)

async def get_orders(date_string, product_ids_list, st_datetime, en_datetime, db:AsyncSession):
    ProductAlias = aliased(Product)
    query = select(Order, ProductAlias).where(
        and_(
            Order.date >= st_datetime,
            Order.date <= en_datetime
        )
    ).join(
        ProductAlias,
        ProductAlias.id == func.any(Order.product_id)
    )

    if product_ids_list:
        query = query.where(
            Order.product_id.op('&&')(cast(product_ids_list, ARRAY(BigInteger)))
        )
    result = await db.execute(query)
    orders_with_products = result.fetchall()

    total_units = 0
    total_refund = 0
    total_net_profit = 0
    total_refund = await get_return(st_datetime, en_datetime, db)

    for order, product in orders_with_products:
        total_units += sum(order.quantity)
        product_ids = order.product_id
        quantities = order.quantity
        for i in range(len(product_ids)):
            total_net_profit += (product.sale_price - product.price - product.internal_shipping_price) * quantities[i]
        
    return {
        "date_string": date_string,
        "total_units": total_units,
        "total_refund": total_refund,
        "total_net_profit": total_net_profit,
        "orders": [OrderRead.from_orm(order) for order, _ in orders_with_products]
    }

async def get_PL(date_string, product_ids_list, st_datetime, en_datetime, db:AsyncSession):
    ProductAlias = aliased(Product)
    query = select(Order, ProductAlias).where(
        and_(
            Order.date >= st_datetime,
            Order.date <= en_datetime
        )
    ).join(
        ProductAlias,
        ProductAlias.id == func.any(Order.product_id)
    )

    if product_ids_list:
        query = query.where(
            Order.product_id.op('&&')(cast(product_ids_list, ARRAY(BigInteger)))
        )
    result = await db.execute(query)
    orders_with_products = result.fetchall()
    sales = 0
    units_sold = 0
    refunds = await get_return(st_datetime, en_datetime, db)
    

    return

@router.get('/tiles')

async def get_dashboard_info(db: AsyncSession = Depends(get_db)):
    today = datetime.date.today()
    orders_today_data = await get_value(today, today, db)

    yesterday = datetime.date.today() - datetime.timedelta(days = 1)
    orders_yesterday_data = await get_value(yesterday, yesterday, db)
    
    first_day_of_month = datetime.date(today.year, today.month, 1)
    orders_month_data = await get_value(first_day_of_month, today, db)

    orders_forecast_data = await forecast(first_day_of_month, today, db)

    if today.month > 1:
        last_month_st = datetime.date(today.year, today.month - 1, 1)
        last_month_en = first_day_of_month - datetime.timedelta(days = 1)
    else:
        last_month_st = datetime.date(today.year - 1, 12, 1)
        last_month_en = datetime.date(today.year - 1, 12, 31)
    orders_last_month_data = await get_value(last_month_st, last_month_en, db)

    return {
        "orders_today_data": { "title": "Today", **orders_today_data },
        "orders_yesterday_data": { "title": "Yesterday", **orders_yesterday_data },
        "orders_month_data": { "title": "This month", **orders_month_data },
        "orders_forecast_data": {"title": "Forecast", **orders_forecast_data},
        "orders_last_month_data": { "title": "Last month", **orders_last_month_data },
    }

async def get_value(st_date, en_date, db:AsyncSession):
    st_datetime = datetime.datetime.combine(st_date, datetime.time.min)
    en_datetime = datetime.datetime.combine(en_date, datetime.time.max)
    
    ProductAlias = aliased(Product)

    query = select(Order, ProductAlias).where(
        and_(
            Order.date >= st_datetime,
            Order.date <= en_datetime
        )
    ).join(
        ProductAlias,
        ProductAlias.id == func.any(Order.product_id)
    )
    
    result = await db.execute(query)
    orders_with_products = result.fetchall()

    date_string = ""
    if st_date == en_date:
        date_string = f"{st_date.day} {st_date.strftime('%B')} {st_date.year}"
    else:
        date_string = f"{st_date.day}-{en_date.day} {st_date.strftime('%B')} {st_date.year}"

    total_sales = 0
    total_orders = len(orders_with_products)
    total_units = 0
    total_refund = await get_return(st_datetime, en_datetime, db)
    total_gross_profit = 0
    total_net_profit = 0
    for order, product in orders_with_products:
        product_ids = order.product_id
        quantities = order.quantity
        total_units += sum(quantity for quantity in quantities)

        for i in range(len(product_ids)): 
            total_sales += product.sale_price * quantities[i]
            total_gross_profit += (product.sale_price - product.price) * quantities[i]
            total_net_profit += (product.sale_price - product.price - product.internal_shipping_price) * quantities[i]

    return {
        "date_range": date_string,
        "total_sales": total_sales,
        "total_orders": total_orders,
        "total_units": total_units,
        "total_refund": total_refund,
        "total_gross_profit": total_gross_profit,
        "total_net_profit": total_net_profit,
    }
    
async def forecast(st_date, en_date, db: AsyncSession):
    st_datetime = datetime.datetime.combine(st_date, datetime.time.min)
    en_datetime = datetime.datetime.combine(en_date, datetime.time.max)

    result = await db.execute(select(Order).where(Order.date >= st_datetime, Order.date <= en_datetime))
    orders = result.scalars().all()
    if not orders:
        return {
            "date_range": f"Forecast for {st_date.strftime('%B')} {st_date.year}",
            "total_sales": 0.0,
            "total_orders": 0,
            "total_units": 0,
            "total_refund": 0,
            "total_gross_profit": 0,
            "total_net_profit": 0,
        }
    
    present_data = await get_value(st_datetime, en_datetime, db)

    total_sales = present_data.get("total_sales")
    total_orders = present_data.get("total_orders")
    total_units = present_data.get("total_units")
    total_refund = present_data.get("total_refund")
    total_gross_profit = present_data.get("total_gross_profit")
    total_net_profit = present_data.get("total_net_profit")

    days_passed = (en_date - st_date).days + 1
    total_days_in_month = (datetime.date(st_date.year, st_date.month + 1, 1) - st_date).days if st_date.month < 12 else 31
    days_remaining = total_days_in_month - days_passed

    avg_daily_sales = total_sales / days_passed
    avg_daily_orders = total_orders / days_passed
    avg_daily_units = total_units / days_passed
    avg_daily_refund = total_refund / days_passed
    avg_daily_gross_profit = total_gross_profit / days_passed
    avg_daily_net_profit = total_net_profit / days_passed

    forecasted_sales = total_sales + (avg_daily_sales * days_remaining)
    forecasted_orders = int(total_orders + (avg_daily_orders * days_remaining))
    forecasted_units = int(total_units + (avg_daily_units * days_remaining))
    forecasted_refund = int(total_refund + (avg_daily_refund * days_remaining))
    forecasted_gross_profit = total_gross_profit + (avg_daily_gross_profit * days_remaining)
    forecasted_net_profit = total_net_profit + (avg_daily_net_profit * days_remaining)

    return {
        "date_range": f"Forecast for {st_date.strftime('%B')} {st_date.year}",
        "total_sales": forecasted_sales,
        "total_orders": forecasted_orders,
        "total_units": forecasted_units,
        "total_refund": forecasted_refund,
        "total_gross_profit": forecasted_gross_profit,
        "total_net_profit": forecasted_net_profit,
    }

@router.get('/chart')
async def get_chart_data(
    product_ids: str = Query(None),  # Make product_ids required
    type: int = Query(...),  # Make type required
    db: AsyncSession = Depends(get_db)
):
    
    today = datetime.date.today()
    print("*****************")
    chart_data = []

    if product_ids:
        product_ids_list = [int(id.strip()) for id in product_ids.split(",")]
    else:
        product_ids_list = []

    if type == 1:
        for i in range(13):
            if today.month + i <= 12:
                date = datetime.date(today.year - 1, today.month + i, today.day)
            else:
                date = datetime.date(today.year, today.month + i - 12, today.day)

            chart_data.append(await get_month_data(product_ids_list, date, db))
    elif type == 2:
        week_num_en = today.isocalendar()[1]
        en_date = today
        st_date = today - datetime.timedelta(today.weekday())
        for i in range(14):
            if week_num_en - i > 0:
                week_string = f"week {week_num_en - i}"
            else:
                week_string = f"week {week_num_en + 52 - i}"

            chart_data.insert(0, await get_week_data(week_string, product_ids_list, st_date, en_date, db))
            en_date = st_date - datetime.timedelta(days=1)
            st_date = st_date - datetime.timedelta(days=7)
    else:
        for i in range(30):
            date = today - datetime.timedelta(days=i)
            chart_data.insert(0, await get_day_data(date, product_ids_list, db))
    return {
        "chart_data": chart_data
    }

async def get_month_data(product_ids_list, date, db: AsyncSession):
    date_string = f"{date.strftime('%b')} {date.year}"
    st_date = datetime.date(date.year, date.month, 1)
    if date.month == 12:
        en_date = datetime.date(date.year, 12, 31)
    else:
        en_date = datetime.date(date.year, date.month + 1, 1) - datetime.timedelta(days = 1)

    st_datetime = datetime.datetime.combine(st_date, datetime.time.min)
    en_datetime = datetime.datetime.combine(en_date, datetime.time.max)

    return await get_orders(date_string, product_ids_list, st_datetime, en_datetime, db)

async def get_week_data(week_string, product_ids_list, st_date, en_date, db: AsyncSession):
    st_datetime = datetime.datetime.combine(st_date, datetime.time.min)
    en_datetime = datetime.datetime.combine(en_date, datetime.time.max)

    return await get_orders(week_string, product_ids_list, st_datetime, en_datetime, db)

async def get_day_data(date, product_ids_list, db: AsyncSession):
    st_datetime = datetime.datetime.combine(date, datetime.time.min)
    en_datetime = datetime.datetime.combine(date, datetime.time.max)
    date_string = f"{date.day} {date.strftime('%b')} {date.year}"

    return await get_orders(date_string, product_ids_list, st_datetime, en_datetime, db)

@router.get('/P_L')
async def get_PL_data(product_ids: str = Query(None),  # Make product_ids required
    type: int = Query(...),  # Make type required
    db: AsyncSession = Depends(get_db)
):
    today = datetime.date.today()
    PL_data = []

    if product_ids:
        product_ids_list = [int(id.strip()) for id in product_ids.split(",")]
    else:
        product_ids_list = []

    if type == 1:
        for i in range(13):
            if today.month + i <= 12:
                date = datetime.date(today.year - 1, today.month + i, today.day)
            else:
                date = datetime.date(today.year, today.month + i - 12, today.day)

            PL_data.insert(0, await PL_month_data(product_ids_list, date, db))
    elif type == 2:
        week_num_en = today.isocalendar()[1]
        en_date = today
        st_date = today - datetime.timedelta(today.weekday())
        for i in range(14):
            if week_num_en - i > 0:
                week_string = f"week {week_num_en - i}"
            else:
                week_string = f"week {week_num_en + 52 - i}"

            PL_data.append(await PL_week_data(week_string, product_ids_list, st_date, en_date, db))
            en_date = st_date - datetime.timedelta(days=1)
            st_date = st_date - datetime.timedelta(days=7)
    else:
        for i in range(30):
            date = today - datetime.timedelta(days=i)
            PL_data.append(await PL_day_data(date, product_ids_list, db))
    return {
        "PL_data": PL_data
    }

async def PL_month_data(product_ids_list, date, db: AsyncSession):
    month_string = f"{date.strftime('%b')} {date.year}"
    st_date = datetime.date(date.year, date.month, 1)
    if date.month == 12:
        en_date = datetime.date(date.year, 12, 31)
    else:
        en_date = datetime.date(date.year, date.month + 1, 1) - datetime.timedelta(days = 1)

    st_datetime = datetime.datetime.combine(st_date, datetime.time.min)
    en_datetime = datetime.datetime.combine(en_date, datetime.time.max)

    query = select(Order).where(Order.date >= st_datetime, Order.date <= en_datetime)
    if product_ids_list:
        query = query.where(Order.product_id.in_(product_ids_list))

    result = await db.execute(query)
    orders = result.scalars().all() 

    total_sales = sum(order.sales for order in orders)
    total_units = sum(order.unit for order in orders)
    total_refund = sum(order.refunded_amount for order in orders)
    total_gross_profit = sum(order.gross_profit for order in orders)
    total_net_profit = sum(order.net_profit for order in orders)

    return {
        "date_string": month_string,
        "total_sales": total_sales,
        "total_units": total_units,
        "total_refund": total_refund,
        "total_gross_profit": total_gross_profit,
        "total_net_profit": total_net_profit,
        "orders": [OrderRead.from_orm(order) for order in orders]
    }

async def PL_week_data(week_string, product_ids_list, st_date, en_date, db: AsyncSession):
    st_datetime = datetime.datetime.combine(st_date, datetime.time.min)
    en_datetime = datetime.datetime.combine(en_date, datetime.time.max)

    query = select(Order).where(Order.date >= st_datetime, Order.date <= en_datetime)
    if product_ids_list:
        query = query.where(Order.product_id.in_(product_ids_list))

    result = await db.execute(query)
    orders = result.scalars().all() 

    total_sales = sum(order.sales for order in orders)
    total_units = sum(order.unit for order in orders)
    total_refund = sum(order.refunded_amount for order in orders)
    total_gross_profit = sum(order.gross_profit for order in orders)
    total_net_profit = sum(order.net_profit for order in orders)
    
    return {
        "date_string": week_string,
        "total_sales": total_sales,
        "total_units": total_units,
        "total_refund": total_refund,
        "total_gross_profit": total_gross_profit,
        "total_net_profit": total_net_profit,
        "orders": [OrderRead.from_orm(order) for order in orders]
    }

async def PL_day_data(date, product_ids_list, db: AsyncSession):
    day_string = f"{date.day} {date.strftime('%b')} {date.year}"
    st_datetime = datetime.datetime.combine(date, datetime.time.min)
    en_datetime = datetime.datetime.combine(date, datetime.time.max)

    query = select(Order).where(Order.date >= st_datetime, Order.date <= en_datetime)
    if product_ids_list:
        query = query.where(Order.product_id.in_(product_ids_list))

    result = await db.execute(query)
    orders = result.scalars().all() 

    total_sales = sum(order.sales for order in orders)
    total_units = sum(order.unit for order in orders)
    total_refund = sum(order.refunded_amount for order in orders)
    total_gross_profit = sum(order.gross_profit for order in orders)
    total_net_profit = sum(order.net_profit for order in orders)
    
    return {
        "date_string": day_string,
        "total_sales": total_sales,
        "total_units": total_units,
        "total_refund": total_refund,
        "total_gross_profit": total_gross_profit,
        "total_net_profit": total_net_profit,
        "orders": [OrderRead.from_orm(order) for order in orders]
    }

# @router.get('/trends')