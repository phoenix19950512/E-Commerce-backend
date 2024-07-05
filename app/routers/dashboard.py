from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.models.orders import Order
from app.schemas.orders import OrderRead
from typing import List, Optional
from app.database import get_db
import datetime

router = APIRouter()
# @router.post("/", response_model=ProductRead)
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
        "orders_month_data": { "title": "Month to Date", **orders_month_data },
        "orders_forecast_data": { "title": "This Month (forcast)", **orders_forecast_data },
        "orders_last_month_data": { "title": "Last Month", **orders_last_month_data }
    }

async def get_value(st_date, en_date, db: AsyncSession = Depends(get_db)):
    st_datetime = datetime.datetime.combine(st_date, datetime.time.min)
    en_datetime = datetime.datetime.combine(en_date, datetime.time.max)
    
    date_string = ""
    if st_date == en_date:
        date_string = f"{st_date.day} {st_date.strftime('%B')} {st_date.year}"
    else:
        date_string = f"{st_date.day}-{en_date.day} {st_date.strftime('%B')} {st_date.year}"

    result = await db.execute(select(Order).options(joinedload(Order.owner)).where(Order.date >= st_datetime, Order.date <= en_datetime))

    orders = result.scalars().all()

    total_sales = sum(order.sales for order in orders)
    total_orders = len(orders)
    total_units = sum(order.unit for order in orders)
    total_refund = sum(order.refunded_amount for order in orders)
    total_gross_profit = sum(order.gross_profit for order in orders)
    total_net_profit = sum(order.net_profit for order in orders)

    unique_product_ids = set()
    total_ads = 0
    for order in orders:
        if order.product_id not in unique_product_ids:
            unique_product_ids.add(order.product_id)
            total_ads += order.owner.commission
    total_payout = total_sales - total_ads
    return {
        "date_range": date_string,
        "total_sales": total_sales,
        "total_orders": total_orders,
        "total_units": total_units,
        "total_refund": total_refund,
        "total_payout": total_payout,
        "total_gross_profit": total_gross_profit,
        "total_net_profit": total_net_profit,
        "orders": [OrderRead.from_orm(order) for order in orders]
    }
    
async def forecast(st_date, en_date, db: AsyncSession):
    st_datetime = datetime.datetime.combine(st_date, datetime.time.min)
    en_datetime = datetime.datetime.combine(en_date, datetime.time.max)

    result = await db.execute(select(Order).options(joinedload(Order.owner)).where(Order.date >= st_datetime, Order.date <= en_datetime))
    orders = result.scalars().all()
    if not orders:
        return {
            "date_range": f"Forecast for {st_date.strftime('%B')} {st_date.year}",
            "total_sales": 0.0,
            "total_orders": 0,
            "total_units": 0,
            "total_refund": 0,
            "total_payout": 0,
            "total_gross_profit": 0,
            "total_net_profit": 0,
        }
    
    total_sales = sum(order.sales for order in orders)
    total_orders = len(orders)
    total_units = sum(order.unit for order in orders)
    total_refund = sum(order.refunded_amount for order in orders)
    total_gross_profit = sum(order.gross_profit for order in orders)
    total_net_profit = sum(order.net_profit for order in orders)
    unique_product_ids = set()
    total_ads = 0
    for order in orders:
        if order.product_id not in unique_product_ids:
            unique_product_ids.add(order.product_id)
            total_ads += order.owner.commission

    days_passed = (en_date - st_date).days + 1
    total_days_in_month = (datetime.date(st_date.year, st_date.month + 1, 1) - st_date).days if st_date.month < 12 else 31
    days_remaining = total_days_in_month - days_passed

    avg_daily_sales = total_sales / days_passed
    avg_daily_orders = total_orders / days_passed
    avg_daily_units = total_units / days_passed
    avg_daily_refund = total_refund / days_passed
    avg_daily_ads = total_ads / days_passed
    avg_daily_gross_profit = total_gross_profit / days_passed
    avg_daily_net_profit = total_net_profit / days_passed

    forecasted_sales = total_sales + (avg_daily_sales * days_remaining)
    forecasted_orders = total_orders + (avg_daily_orders * days_remaining)
    forecasted_units = total_units + (avg_daily_units * days_remaining)
    forecasted_refund = total_refund + (avg_daily_refund * days_remaining)
    forecasted_ads = total_ads + (avg_daily_ads * days_remaining)
    forecasted_payout = forecasted_sales - forecasted_ads
    forecasted_gross_profit = total_gross_profit + (avg_daily_gross_profit * days_remaining)
    forecasted_net_profit = total_net_profit + (avg_daily_net_profit * days_remaining)

    return {
        "date_range": f"Forecast for {st_date.strftime('%B')} {st_date.year}",
        "total_sales": forecasted_sales,
        "total_orders": forecasted_orders,
        "total_units": forecasted_units,
        "total_refund": forecasted_refund,
        "total_payout": forecasted_payout,
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

    query = select(Order).where(Order.date >= st_datetime, Order.date <= en_datetime)
    if product_ids_list:
        query = query.where(Order.product_id.in_(product_ids_list))

    result = await db.execute(query)
    orders = result.scalars().all() 

    total_units = sum(order.unit for order in orders)
    total_refund = sum(order.refunded_amount for order in orders)
    total_net_profit = sum(order.net_profit for order in orders)

    return {
        "date_string": date_string,
        "total_units": total_units,
        "total_refund": total_refund,
        "total_net_profit": total_net_profit,
        "month_orders": [OrderRead.from_orm(order) for order in orders]
    }

async def get_week_data(weeK_string, product_ids_list, st_date, en_date, db: AsyncSession):
    st_datetime = datetime.datetime.combine(st_date, datetime.time.min)
    en_datetime = datetime.datetime.combine(en_date, datetime.time.max)

    query = select(Order).where(Order.date >= st_datetime, Order.date <= en_datetime)
    if product_ids_list:
        query = query.where(Order.product_id.in_(product_ids_list))

    result = await db.execute(query)
    orders = result.scalars().all() 

    total_units = sum(order.unit for order in orders)
    total_refund = sum(order.refunded_amount for order in orders)
    total_net_profit = sum(order.net_profit for order in orders)
    return {
        "weeK_string": weeK_string,
        "total_units": total_units,
        "total_refund": total_refund,
        "total_net_profit": total_net_profit,
        "week_orders": [OrderRead.from_orm(order) for order in orders]
    }

async def get_day_data(date, product_ids_list, db: AsyncSession):
    st_datetime = datetime.datetime.combine(date, datetime.time.min)
    en_datetime = datetime.datetime.combine(date, datetime.time.max)

    query = select(Order).where(Order.date >= st_datetime, Order.date <= en_datetime)
    if product_ids_list:
        query = query.where(Order.product_id.in_(product_ids_list))

    result = await db.execute(query)
    orders = result.scalars().all() 

    total_units = sum(order.unit for order in orders)
    total_refund = sum(order.refunded_amount for order in orders)
    total_net_profit = sum(order.net_profit for order in orders)

    return {
        "day_string": f"{date.day} {date.strftime('%b')} {date.year}",
        "total_units": total_units,
        "total_refund": total_refund,
        "total_net_profit": total_net_profit,
        "day_orders": [OrderRead.from_orm(order) for order in orders]
    }

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
        "month_string": month_string,
        "total_sales": total_sales,
        "total_units": total_units,
        "total_refund": total_refund,
        "total_gross_profit": total_gross_profit,
        "total_net_profit": total_net_profit,
        "month_orders": [OrderRead.from_orm(order) for order in orders]
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
        "week_string": week_string,
        "total_sales": total_sales,
        "total_units": total_units,
        "total_refund": total_refund,
        "total_gross_profit": total_gross_profit,
        "total_net_profit": total_net_profit,
        "week_orders": [OrderRead.from_orm(order) for order in orders]
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
        "day_string": day_string,
        "total_sales": total_sales,
        "total_units": total_units,
        "total_refund": total_refund,
        "total_gross_profit": total_gross_profit,
        "total_net_profit": total_net_profit,
        "day_orders": [OrderRead.from_orm(order) for order in orders]
    }

# @router.get('/trends')