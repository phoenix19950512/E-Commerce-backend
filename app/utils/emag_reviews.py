import logging
import requests
import base64
from app.models.product import Product
from app.models.marketplace import Marketplace
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from bs4 import BeautifulSoup
PROXIES = {
    'http': 'http://Gb7Pib5JMe4BDolM8jsY8RondrahTp:iWCCSqNRkZQxqikn_country-ro@proxy.resi.gg:8082',
    'https': 'http://Gb7Pib5JMe4BDolM8jsY8RondrahTp:iWCCSqNRkZQxqikn_country-ro@proxy.resi.gg:8082',
}

async def get_review_by_product(product_id, product_part_number_key):
    url = f'https://www.emag.ro/product-feedback/{product_id}/pd/{product_part_number_key}/reviews/list'
    print('------------------', url)

    response = requests.get(url, proxies=PROXIES)
    
    if response.status_code == 200:
        logging.info("success count")
        return response.json()
    else:
        logging.error(f"Failed to retrieve reviews from product '{product_part_number_key}': {response.status_code}")
        return None

async def get_all_reviews(product_id_list, product_part_number_key_list):
    result = []
    for i in range(len(product_id_list)):
        try:
            result.append({
                "product_id": product_id_list[i],
                "reviews": await get_review_by_product(product_id_list[i], product_part_number_key_list[i])
            })
        except Exception as e:
            logging.error('Failed to retrieve reviews')
            result.append({
                "product_id": product_id_list[i],
                "reviews": []
            })
    return result

async def refresh_reviews(marketplace: Marketplace, db:AsyncSession):
    result = await db.execute(select(Product))
    products = result.scalars().all()

    product_id_list = []
    product_part_number_key_list = []
    for product in products:
        product_id_list.append(product.id)
        product_part_number_key_list.append(product.part_number_key)

    reviews = await get_all_reviews(product_id_list, product_part_number_key_list)

    return reviews