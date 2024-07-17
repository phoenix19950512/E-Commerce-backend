from fastapi import FastAPI, HTTPException # type: ignore
from pydantic import BaseModel # type: ignore
from typing import List, Dict
import psycopg2
from psycopg2 import sql
from app.models.product import Product
from app.models.notifications import Notification
from app.routers.notifications import create_new_notification
from app.utils.emag_reviews import *
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.config import settings
from datetime import datetime

app = FastAPI()

initial_products = [
    {"id": "1", "seller": "SellerA", "price": 100, "stock": 50},
    {"id": "2", "seller": "SellerB", "price": 150, "stock": 30},
]

initial_reviews = [
    {"id": "1", "user_id": "1", "review_text": "Great product!", "rating": 5},
    {"id": "1", "user_id": "1", "review_text": "Not as expected", "rating": 2},
    {"id": "2", "user_id": "1", "review_text": "Excellent quality", "rating": 4},
    {"id": "2", "user_id": "1", "review_text": "Terrible, broke after a week", "rating": 1},
]

# Store initial state in a dictionary for easy lookup
product_state = {product['id']: product for product in initial_products}
review_state = {review['id']: [] for review in initial_reviews}
for review in initial_reviews:
    review_state[review['id']].append(review)

class Review(BaseModel):
    product_id: str
    review_text: str
    rating: int

def check_hijacker(product_list: List[Product]):
    hijackers = []
    try:
        for product in product_list:
            product_id = product.id
            if product.buy_button_rank == None:
                continue
            if product.buy_button_rank > 1:
                hijackers.append({
                        "product_id": product_id,
                        "name": product.product_name,
                        "ean": product.ean
                    })
        
        logging.info("############Success to read hijackers")
        return hijackers
    except Exception as e:
        logging.info("Can't Read hijackers", e)

def check_bad_reviews(review_list: List[Review], threshold: int = 3):
    bad_reviews = []

    for review in review_list.reviews:
        if review.rating <= threshold:
            bad_reviews.append(review)

    return bad_reviews
async def check_hijacker_and_bad_reviews(marketplace: Marketplace, db: AsyncSession):
    conn = psycopg2.connect(
        dbname=settings.DB_NAME,
        user=settings.DB_USERNAME,
        password=settings.DB_PASSOWRD,
        host=settings.DB_URL,
        port=settings.DB_PORT
    )
    conn.set_client_encoding('UTF8')
    
    result = await db.execute(select(Product))
    products = result.scalars().all()

    logging.info("Start checking hijacker")
    hijackers = check_hijacker(products)

    print(hijackers)
    admin_id = 1

    try:
        cursor = conn.cursor()

        # delete_notifications_query = sql.SQL("DELETE FROM {}").format(sql.Identifier("notifications"))
        # cursor.execute(delete_notifications_query)

        insert_notification_query = sql.SQL("""
            INSERT INTO {} (
                title,
                description,
                time,
                ean,
                state,
                read,
                user_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s                          
            ) ON CONFLICT (ean) DO UPDATE SET
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

            values = (
                title,
                description,
                time,
                ean,
                state,
                read,
                user_id
            )

            cursor.execute(insert_notification_query, values)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Can't add notification", e)

    reviews = await refresh_reviews(marketplace, db)


    print("##############", len(reviews))

    bad_reviews = check_bad_reviews(reviews)
    
    print("@@@@@@@@@@@@@@@@", bad_reviews)
    # for bad_review in bad_reviews:
    #     date_str = datetime.now()
    #     create_new_notification({
    #         "title": "Warning",
    #         "description": "Never send bad review again!",
    #         "time": date_str.strftime('%Y-%m-%dT%H:%M:%S'),
    #         "state": "warning",
    #         "read": False,
    #         "user_id": bad_review.user_id
    #     })