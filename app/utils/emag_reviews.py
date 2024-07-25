import logging
import requests
import base64
from app.models.product import Product
from app.models.marketplace import Marketplace
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import psycopg2
from app.config import settings
from psycopg2 import sql


PROXIES = {
    'http': 'http://Gb7Pib5JMe4BDolM8jsY8RondrahTp:iWCCSqNRkZQxqikn_country-ro@proxy.resi.gg:8082',
    'https': 'http://Gb7Pib5JMe4BDolM8jsY8RondrahTp:iWCCSqNRkZQxqikn_country-ro@proxy.resi.gg:8082',
}

async def get_review_by_product(product_id, product_part_number_key, marketplace: Marketplace):
    url = f'{marketplace.baseURL.replace("marketplace", "www")}/product-feedback/{product_id}/pd/{product_part_number_key}/reviews/list'
    print('------------------', url)

    response = requests.get(url, proxies=PROXIES)
    
    if response.status_code == 200:
        logging.info("success count")
        return response.json()
    else:
        logging.error(f"Failed to retrieve reviews from product '{product_part_number_key}': {response.status_code}")
        return "nothing"

async def get_all_reviews(product_id_list, product_part_number_key_list, marketplace: Marketplace):
    result = []
    for i in range(len(product_id_list)):
        try:
            result.append({
                "product_id": product_id_list[i],
                "reviews": await get_review_by_product(product_id_list[i], product_part_number_key_list[i], marketplace)
            })
        except Exception as e:
            logging.error('Failed to retrieve reviews')
            result.append({
                "product_id": product_id_list[i],
                "reviews": []
            })
    return await get_review_by_product(product_id_list[i], product_part_number_key_list[i], marketplace)

async def insert_review_into_db(review, place):
    try:
        conn = psycopg2.connect(
            dbname=settings.DB_NAME,
            user=settings.DB_USERNAME,
            password=settings.DB_PASSOWRD,  # Corrected spelling from DB_PASSOWRD to DB_PASSWORD
            host=settings.DB_URL,
            port=settings.DB_PORT
        )
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()

        insert_query = sql.SQL("""
            INSERT INTO {} (
                product_id,
                review_id,
                user_id,
                user_name,
                content,
                moderated_by,
                rating,
                brand_id,
                review_marketplace               
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (id, review_id, review_marketplace) DO UPDATE SET
                product_id = EXCLUDED.product_id,
                user_id = EXCLUDED.user_id,
                user_name = EXCLUDED.user_name,
                content = EXCLUDED.content,
                moderated_by = EXCLUDED.moderated_by,
                rating = EXCLUDED.rating,
                brand_id = EXCLUDED.brand_id
        """).format(sql.Identifier("reviews"))

        product_id = review.get("product", {}).get("id")
        review_id = review.get("id")
        user_id = review.get("user", {}).get("id")
        user_name = review.get("user", {}).get("name")
        content = review.get("content")
        moderated_by = review.get("moderated_by")
        rating = review.get("rating")
        brand_id = review.get("brand_id")
        review_marketplace = place

        values = (
            product_id,
            review_id,
            user_id,
            user_name,
            content,
            moderated_by,
            rating,
            brand_id,
            review_marketplace
        )

        print(f'Inserting review: {values}')
        cursor.execute(insert_query, values)
        conn.commit()
        print(f"Successfully inserted review: {values}")

        cursor.close()
        conn.close()
    except Exception as inner_e:
        print(f"Error inserting review {review_id}: {inner_e}")

async def insert_reviews_into_db(reviews, place):
    for review in reviews:
        await insert_review_into_db(review, place)

async def refresh_reviews(marketplace: Marketplace, db: AsyncSession):
    result = await db.execute(select(Product))
    products = result.scalars().all()

    logging.info(f"Number of products: {len(products)}")

    cnt = 0
    try:
        for product in products:
            cnt += 1
            logging.info(f"Processing product {cnt}/{len(products)}: {product.id}")

            result = await get_review_by_product(product.id, product.part_number_key, marketplace)

            if result == "nothing" or result.get("reviews").get("count") == 0:
                logging.info(f"No reviews for product {product.id}")
                continue

            reviews = result.get("reviews").get("items")

            await insert_reviews_into_db(reviews, marketplace.marketplaceDomain)
        
        logging.info(f"Processed {cnt} products")
    except Exception as e:
        logging.error(f"Error processing reviews: {e}")

    print(cnt)