from fastapi import FastAPI, HTTPException # type: ignore
from pydantic import BaseModel # type: ignore
from typing import List, Dict
import psycopg2
from psycopg2 import sql
from app.models.product import Product
from app.models.notifications import Notification
from app.models.review import Review
from app.routers.notifications import create_new_notification
from app.utils.emag_reviews import *
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.config import settings
from sqlalchemy import text
from datetime import datetime

app = FastAPI()

# def create_notifications_table(notifications_table):
#     conn = psycopg2.connect(
#         dbname=settings.DB_NAME,
#         user=settings.DB_USERNAME,
#         password=settings.DB_PASSOWRD,
#         host=settings.DB_URL,
#         port=settings.DB_PORT
#     )
#     cursor = conn.cursor()
#     create_table_query = sql.SQL("""
#         CREATE TABLE IF NOT EXISTS {} (
#             id SERIAL PRIMARY KEY,
#             title TEXT,
#             description TEXT,
#             time TIMESTAMP,
#             ean TEXT UNIQUE,
#             state TEXT,
#             read BOOLEAN,
#             user_id INTEGER,
#             market_place TEXT                    
#         )"""
#     ).format(sql.Identifier(notifications_table))
#     cursor.execute(create_table_query)
#     conn.commit()
#     cursor.close()
#     conn.close()

def check_hijacker(product_list):
    hijackers = []
    try:
        for product in product_list:
            product_id = product.get("id")

            buy_button_rank = product.get("buy_button_rank")
            # for i in range(len(buy_button_ranks)):
            if buy_button_rank == None:
                continue
            if buy_button_rank > 1:
                hijackers.append({
                        "product_id": product_id,
                        "name": product.get("name"),
                        "ean": product.get("ean")
                    })
        
        logging.info("############Success to read hijackers")
        return hijackers
    except Exception as e:
        logging.info("Can't Read hijackers", e)

def check_bad_reviews(review_list: List[Review], threshold: int = 3):
    bad_reviews = []

    for review in review_list:
        if review.rating <= threshold:
            bad_reviews.append(review)

    return bad_reviews

async def check_hijacker_and_bad_reviews(marketplace: Marketplace, db: AsyncSession):
    products_table = f"{marketplace.marketplaceDomain.replace('.', '_')}_products".lower()
    notifications_table = f"{marketplace.marketplaceDomain.replace('.', '_')}_notifications".lower()
    settings.notifications_table_name.append(notifications_table)
    reviews_table = f"{marketplace.marketplaceDomain.replace('.', '_')}_reviews".lower()
    settings.reviews_table_name.append(reviews_table)
    conn = psycopg2.connect(
        dbname=settings.DB_NAME,
        user=settings.DB_USERNAME,
        password=settings.DB_PASSOWRD,
        host=settings.DB_URL,
        port=settings.DB_PORT
    )
    conn.set_client_encoding('UTF8')
    
    result = await db.execute(text(f"SELECT * FROM {products_table}"))
    products = result.fetchall()

    product_dicts = []
    for product in products:
        product_dict = {key: value for key, value in zip(result.keys(), product)}
        product_dicts.append(product_dict)

    logging.info("Start checking hijacker")

    hijackers = check_hijacker(product_dicts)

    print(hijackers)

    result = await db.execute(select(Notification))
    notifications = result.scalars().all()
    
    id = len(notifications) + 1

    admin_id = 1

    cursor = conn.cursor()

    # delete_notifications_query = sql.SQL("DELETE FROM {}").format(sql.Identifier("notifications"))
    # cursor.execute(delete_notifications_query)
    try:
        insert_notification_query = sql.SQL("""
            INSERT INTO {} (
                id,
                title,
                description,
                time,
                ean,
                state,
                read,
                user_id,
                market_place
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s                          
            ) ON CONFLICT (ean, market_place) DO UPDATE SET
                time = EXCLUDED.time,
                user_id = EXCLUDED.user_id       
        """).format(sql.Identifier("notifications"))

        
        for hijacker in hijackers:
            date_str = datetime.now()            
            title = "Detected Hijacker"
            description = hijacker["name"]
            time = date_str.strftime('%Y-%m-%dT%H:%M:%S')
            ean = hijacker["ean"]
            state = "error"
            read = False
            user_id = admin_id
            market_place = marketplace.marketplaceDomain.lower()

            values = (
                id,
                title,
                description,
                time,
                ean,
                state,
                read,
                user_id,
                market_place
            )

            id += 1

            cursor.execute(insert_notification_query, values)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Can't add notification", e)

    await db.close()
    await refresh_reviews(marketplace, db)

    result = await db.execute(select(Review))
    reviews = result.scalars().all()

    bad_reviews = check_bad_reviews(reviews)
    
    print("@@@@@@@@@@@@@@@@", bad_reviews)
    # # for bad_review in bad_reviews:
    # #     date_str = datetime.now()
    # #     create_new_notification({
    # #         "title": "Warning",
    # #         "description": "Never send bad review again!",
    # #         "time": date_str.strftime('%Y-%m-%dT%H:%M:%S'),
    # #         "state": "warning",
    # #         "read": False,
    # #         "user_id": bad_review.user_id
    # #     })