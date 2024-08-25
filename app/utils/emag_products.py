from psycopg2 import sql
from urllib.parse import urlparse
from app.config import settings
from fastapi import Depends
import requests
import psycopg2
import base64
import urllib
import hashlib
import json
import os
import time
import logging
from app.models.marketplace import Marketplace
from app.models.internal_product import Internal_Product
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.database import get_db
from decimal import Decimal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PROXIES = {
    'http': 'http://p2p_user:jDkAx4EkAyKw@65.109.7.74:54021',
    'https': 'http://p2p_user:jDkAx4EkAyKw@65.109.7.74:54021',
}

def change_string(ean_str):
    if len(ean_str) == 12:
        return '0' + ean_str
    else:
        return ean_str

def count_all_products(MARKETPLACE_API_URL, PRODUCTS_ENDPOINT, COUNT_ENGPOINT, API_KEY, PUBLIC_KEY=None, usePublicKey=False):
    logging.info("counting start")
    url = f"{MARKETPLACE_API_URL}{PRODUCTS_ENDPOINT}/{COUNT_ENGPOINT}"
    if usePublicKey is False:
        api_key = str(API_KEY).replace("b'", '').replace("'", "")
        headers = {
            "Authorization": f"Basic {api_key}",
            "Content-Type": "application/json"
        }
    else:
        headers = {
            "X-Request-Public-Key": f"{PUBLIC_KEY}",
            "X-Request-Signature": f"{API_KEY}"
        }

    response = requests.get(url, headers=headers, proxies=PROXIES)
    if response.status_code == 200:
        logging.info("success count")
        return response.json()
    else:
        logging.error(f"Failed to retrieve products: {response.status_code}")
        return None
    
def get_all_products(MARKETPLACE_API_URL, PRODUCTS_ENDPOINT, READ_ENDPOINT,  API_KEY, currentPage, PUBLIC_KEY=None, usePublicKey=False):
    url = f"{MARKETPLACE_API_URL}{PRODUCTS_ENDPOINT}/{READ_ENDPOINT}"
    if usePublicKey is True:
        headers = {
            "X-Request-Public-Key": f"{PUBLIC_KEY}",
            "X-Request-Signature": f"{API_KEY}"
        }
    elif usePublicKey is False:
        api_key = str(API_KEY).replace("b'", '').replace("'", "")
        headers = {
            "Authorization": f"Basic {api_key}",
            "Content-Type": "application/json"
        }
    data = json.dumps({
        "itemsPerPage": 100,
        "currentPage": currentPage,
    })
    response = requests.post(url, data=data, headers=headers, proxies=PROXIES)
    if response.status_code == 200:
        products = response.json()
        return products
    else:
        logging.info(f"Failed to retrieve products: {response.status_code}")
        return None

async def insert_products(products, mp_name: str):
    try:
        conn = psycopg2.connect(
            dbname=settings.DB_NAME,
            user=settings.DB_USERNAME,
            password=settings.DB_PASSOWRD,
            host=settings.DB_URL,
            port=settings.DB_PORT
        )
        cursor = conn.cursor()
        insert_query = sql.SQL("""
            INSERT INTO {} (
                id,
                part_number_key,
                product_code,
                product_name,
                model_name,
                buy_button_rank,
                price,
                sale_price,
                ean,
                image_link,
                barcode_title,
                masterbox_title,
                link_address_1688,
                price_1688,
                variation_name_1688,
                pcs_ctn,
                weight,
                volumetric_weight,
                dimensions,
                supplier_id,
                english_name,
                romanian_name,
                material_name_en,
                material_name_ro,
                hs_code,
                battery,
                default_usage,
                production_time,
                discontinued,
                stock,
                smartbill_stock,
                damaged_goods, 
                warehouse_id,
                internal_shipping_price,
                market_place
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (ean) DO UPDATE SET
                buy_button_rank = EXCLUDED.buy_button_rank,
                stock = EXCLUDED.stock,
                market_place = array(SELECT DISTINCT unnest(array_cat(EXCLUDED.market_place, internal_products.market_place)))
        """).format(sql.Identifier("internal_products"))

        for product in products:
            id = product.get('id')
            part_number_key = product.get('part_number_key')
            product_code = ""
            product_name = product.get('name')
            model_name = product.get('brand')
            buy_button_rank = product.get('buy_button_rank')
            price = 0
            sale_price = Decimal(product.get('sale_price', '0.0'))
            ean = str(product.get('ean')[0]) if product.get('ean') else None
            logging.info(ean)
            ean = change_string(ean)
            logging.info(ean)
            image_link = product.get('images')[0]['url'] if product.get('images') else None
            barcode_title = ""
            masterbox_title = ""
            link_address_1688 = ""
            price_1688 = Decimal('0')
            variation_name_1688 = ""
            pcs_ctn = ""
            weight_value = product.get('weight')
            if isinstance(weight_value, str):
                weight_value = weight_value.replace(',', '.')  # Handle any comma as decimal separator
            weight = Decimal(weight_value) if weight_value else Decimal('0')
            volumetric_weight = 0
            dimensions = ""
            supplier_id = 0
            english_name = ""
            romanian_name = ""
            material_name_en = ""
            material_name_ro = ""
            hs_code = ""
            battery = False
            default_usage = ""
            production_time = Decimal('0')
            discontinued = False
            stock = int(product.get('stock')[0].get('value') if product.get('stock') else 0)
            smartbill_stock = 0
            damaged_goods = 0
            warehouse_id = 0
            internal_shipping_price = Decimal('0')
            market_place = [mp_name]  # Ensure this is an array to use array_cat

            values = (
                id,
                part_number_key,
                product_code,
                product_name,
                model_name,
                buy_button_rank,
                price,
                sale_price,
                ean,
                image_link,
                barcode_title,
                masterbox_title,
                link_address_1688,
                price_1688,
                variation_name_1688,
                pcs_ctn,
                weight,
                volumetric_weight,
                dimensions,
                supplier_id,
                english_name,
                romanian_name,
                material_name_en,
                material_name_ro,
                hs_code,
                battery,
                default_usage,
                production_time,
                discontinued,
                stock,
                smartbill_stock,
                damaged_goods,
                warehouse_id,
                internal_shipping_price,
                market_place
            )

            cursor.execute(insert_query, values)
            conn.commit()
        
        cursor.close()
        conn.close()
        print("$$$$$$$$$$$$Products inserted into Products successfully")
    except Exception as e:
        print(f"$$$$$$$$$$$$$Failed to insert products into database: {e}")

async def insert_products_into_db(products, username, place):
    try:
        conn = psycopg2.connect(
            dbname=settings.DB_NAME,
            user=settings.DB_USERNAME,
            password=settings.DB_PASSOWRD,
            host=settings.DB_URL,
            port=settings.DB_PORT
        )
        cursor = conn.cursor()
        insert_query = sql.SQL("""
            INSERT INTO {} (
                id,
                part_number_key,
                product_name,
                model_name,
                buy_button_rank,
                price,
                sale_price,
                sku,
                ean,
                image_link,
                barcode_title,
                masterbox_title,
                link_address_1688,
                price_1688,
                variation_name_1688,
                pcs_ctn,
                weight,
                volumetric_weight,
                dimensions,
                supplier_id,
                english_name,
                romanian_name,
                material_name_en,
                material_name_ro,
                hs_code,
                battery,
                default_usage,
                production_time,
                discontinued,
                stock,
                warehouse_id,
                internal_shipping_price,
                product_marketplace
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (ean, product_marketplace) DO UPDATE SET
                sale_price = EXCLUDED.sale_price,
                stock = EXCLUDED.stock
        """).format(sql.Identifier("products"))

        for product in products:
            id = str(product.get('id'))
            part_number_key = product.get('part_number_key')
            product_name = product.get('name')
            model_name = product.get('brand')
            buy_button_rank = product.get('buy_button_rank')
            price = 0
            sale_price = Decimal(product.get('sale_price', '0.0'))
            sku = ""
            ean = str(product.get('ean')[0]) if product.get('ean') else None
            ean = change_string(ean)
            image_link = product.get('images')[0]['url'] if product.get('images') else None
            barcode_title = ""
            masterbox_title = ""
            link_address_1688 = ""
            price_1688 = Decimal('0')
            variation_name_1688 = ""
            pcs_ctn = ""
            weight_value = product.get('weight')
            if isinstance(weight_value, str):
                weight_value = weight_value.replace(',', '.')  # Handle any comma as decimal separator
            weight = Decimal(weight_value) if weight_value else Decimal('0')
            volumetric_weight = 0
            dimensions = ""
            supplier_id = 0
            english_name = ""
            romanian_name = ""
            material_name_en = ""
            material_name_ro = ""
            hs_code = ""
            battery = False
            default_usage = ""
            production_time = Decimal('0')
            discontinued = False
            stock = int(product.get('stock')[0].get('value') if product.get('stock') else 0)
            warehouse_id = 0
            internal_shipping_price = Decimal('0')
            product_marketplace = place  # Ensure this is an array to use array_cat

            values = (
                id,
                part_number_key,
                product_name,
                model_name,
                buy_button_rank,
                price,
                sale_price,
                sku,
                ean,
                image_link,
                barcode_title,
                masterbox_title,
                link_address_1688,
                price_1688,
                variation_name_1688,
                pcs_ctn,
                weight,
                volumetric_weight,
                dimensions,
                supplier_id,
                english_name,
                romanian_name,
                material_name_en,
                material_name_ro,
                hs_code,
                battery,
                default_usage,
                production_time,
                discontinued,
                stock,
                warehouse_id,
                internal_shipping_price,
                product_marketplace
            )
            cursor.execute(insert_query, values)
            conn.commit()
        
        cursor.close()
        conn.close()
        print("Products inserted successfully")
    except Exception as e:
        print(f"Failed to insert products into database: {e}")

async def refresh_emag_products(marketplace: Marketplace):
    # create_database()
    logging.info(f">>>>>>> Refreshing Marketplace : {marketplace.title} <<<<<<<<")

    endpoint = "/product_offer"
    count_point = "/count"
    read_endpoint = "/read"

    if marketplace.credentials["type"] == "user_pass":
        
        USERNAME = marketplace.credentials["firstKey"]
        PASSWORD = marketplace.credentials["secondKey"]
        API_KEY = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode('utf-8'))
        result = count_all_products(marketplace.baseAPIURL, endpoint, count_point, API_KEY)
        if result:
            pages = result['results']['noOfPages']
            items = result['results']['noOfItems']

            print("------------pages--------------", pages)
            print("------------items--------------", items)
            currentPage = 1
            baseAPIURL = marketplace.baseAPIURL
            try:
                while currentPage <= int(pages):
                    products = get_all_products(baseAPIURL, endpoint, read_endpoint, API_KEY, currentPage)

                    logging.info(f">>>>>>> Current Page : {currentPage} <<<<<<<<")
                    if products and not products.get('isError'):
                        await insert_products_into_db(products['results'], USERNAME, marketplace.marketplaceDomain)
                        await insert_products(products['results'], marketplace.marketplaceDomain)
                    currentPage += 1
            except Exception as e:
                print('++++++++++++++++++++++++++++++++++++++++++')
                print(e)
    elif marketplace.credentials["type"] == "pub_priv":
        PUBLIC_KEY = marketplace.credentials["firstKey"]
        PRIVATE_KEY = marketplace.credentials["secondKey"]
        logging.info("starting count")
        result = count_all_products(marketplace.baseAPIURL, marketplace.products_crud["endpoint"], marketplace.products_crud["count"], sign, PUBLIC_KEY, True, proxies=PROXIES)
        if result:
            pages = result['results']['noOfPages']
            currentPage = 1
            while currentPage <= pages:
                products = get_all_products(marketplace.baseAPIURL, marketplace.products_crud["endpoint"], marketplace.products_crud["read"], sign, currentPage, PUBLIC_KEY, True, proxies=PROXIES)
                if products and not products['isError']:
                    insert_products_into_db(products['results'], PUBLIC_KEY)
                    currentPage += 1


def save(MARKETPLACE_API_URL, ENDPOINT, save_ENDPOINT,  API_KEY, data, PUBLIC_KEY=None, usePublicKey=False):
    url = f"{MARKETPLACE_API_URL}{ENDPOINT}/{save_ENDPOINT}"
    if usePublicKey is True:
        headers = {
            "X-Request-Public-Key": f"{PUBLIC_KEY}",
            "X-Request-Signature": f"{API_KEY}"
        }
    elif usePublicKey is False:
        api_key = str(API_KEY).replace("b'", '').replace("'", "")
        headers = {
            "Authorization": f"Basic {api_key}",
            "Content-Type": "application/json"
        }

    response = requests.post(url, data=json.dumps(data), headers=headers, proxies=PROXIES)
    if response.status_code == 200:
        products = response.json()
        return products
    else:
        logging.info(f"Failed to retrieve products: {response.status_code}")
        return None

async def save_product(data, marketplace:Marketplace, db: AsyncSession):
    if marketplace.credentials["type"] == "user_pass":
        USERNAME = marketplace.credentials["firstKey"]
        PASSWORD = marketplace.credentials["secondKey"]
        API_KEY = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode('utf-8'))
        endpoint = marketplace.products_crud['endpoint']
        savepoint = marketplace.products_crud['savepoint']
        result = save(marketplace.baseAPIURL, endpoint, savepoint, API_KEY, data)

    return result

def post_stock_emag(marketplace:Marketplace, product_id:int, stock:int):
    USERNAME = marketplace.credentials["firstKey"]
    PASSWORD = marketplace.credentials["secondKey"]
    API_KEY = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode('utf-8'))
    url = f"{marketplace.baseAPIURL}/offer_stock"
    api_key = str(API_KEY).replace("b'", '').replace("'", "")
    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "resourceId": product_id,
        "value": stock
    })
    response = requests.post(url, data=data, headers=headers, proxies=PROXIES)
    if response.status_code == 200:
        return response.json()
    else:
        return f"Failed to retrieve products: {response.status_code}"