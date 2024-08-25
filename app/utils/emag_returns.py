from psycopg2 import sql
from app.config import settings
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
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from decimal import Decimal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PROXIES = {
    'http': 'http://14a20bb3efda4:d69e723f2d@168.158.127.74:12323',
    'https': 'http://14a20bb3efda4:d69e723f2d@168.158.127.74:12323',
}

def get_attachments(API_KEY):
    url = 'https://marketplace-api.emag.ro/api-3/product_offer/save'
    api_key = str(API_KEY).replace("b'", '').replace("'", "")
    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json"
    }
    
    data = json.dumps({
        "itmesPerPage": 100,
        "currentPage": 1
    })

    response = requests.post(url, data=data, headers=headers, proxies=PROXIES)
    if response.status_code == 200:
        get_attachments = response.json()
        return get_attachments
    else:
        logging.info(f"Failed to retrieve refunds: {response.status_code}")
        return None

def get_all_rmas(MARKETPLACE_API_URL, RMAS_ENDPOINT, READ_ENDPOINT,  API_KEY, currentPage, PUBLIC_KEY=None, usePublicKey=False):
    url = f"{MARKETPLACE_API_URL}{RMAS_ENDPOINT}{READ_ENDPOINT}"
    
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
        "itmesPerPage": 100,
        "currentPage": currentPage
    })
    response = requests.post(url, data=data, headers=headers, proxies=PROXIES)
    if response.status_code == 200:
        rmas = response.json()
        return rmas
    else:
        logging.info(f"Failed to retrieve refunds: {response.status_code}")
        return None

def count_all_rmas(MARKETPLACE_API_URL, RMAS_ENDPOINT, COUNT_ENGPOINT, API_KEY):
    logging.info("counting start")
    url = f"{MARKETPLACE_API_URL}{RMAS_ENDPOINT}{COUNT_ENGPOINT}"

    api_key = str(API_KEY).replace("b'", '').replace("'", "")
    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, proxies=PROXIES)
    if response.status_code == 200:
        logging.info("success rmas count")
        return response.json()
    else:
        logging.error(f"Failed to retrieve rmas: {response.status_code}")
        return None

async def insert_rmas_into_db(rmas, place:str):
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
                emag_id,
                order_id,
                type,
                customer_name,
                customer_company,
                customer_phone,
                products,
                quantity,
                observations,
                pickup_address,
                return_reason,
                return_type,
                replacement_product_emag_id,
                replacement_product_id,
                replacement_product_name,
                replacement_product_quantity,
                date,
                request_status,
                return_market_place,
                awb
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (order_id, return_market_place) DO UPDATE SET
                return_reason = EXCLUDED.return_reason,
                request_status = EXCLUDED.request_status               
        """).format(sql.Identifier("returns"))

        for rma in rmas:
            emag_id = rma.get('emag_id')
            order_id = rma.get('order_id')
            type = rma.get('type')
            customer_name = rma.get('customer_name')
            customer_company = rma.get('customer_company')
            customer_phone = rma.get('customer_phone')
            products = [str(product.get('product_id')) for product in rma.get('products')]
            quantity = [int(product.get('quantity')) for product in rma.get('products')]
            observations = [str(product.get('observations')) for product in rma.get('products')]
            pickup_address = rma.get('pickup_address')
            return_reason = str(rma.get('return_reason'))
            return_type = rma.get('return_type')
            replacement_product_emag_id = rma.get('replacement_product_emag_id')
            replacement_product_id = rma.get('replacement_product_id')
            replacement_product_name = rma.get('replacement_product_name')
            replacement_product_quantity = rma.get('replacement_product_quantity')
            date = rma.get('date')
            request_status = rma.get('request_status')
            return_market_place = place
            awb = ""

            value = (
                emag_id,
                order_id,
                type,
                customer_name,
                customer_company,
                customer_phone,
                products,
                quantity,
                observations,
                pickup_address,
                return_reason,
                return_type,
                replacement_product_emag_id,
                replacement_product_id,
                replacement_product_name,
                replacement_product_quantity,
                date,
                request_status,
                return_market_place,
                awb
            )
            cursor.execute(insert_query, value)
            conn.commit()
        
        cursor.close()
        conn.close()
        logging.info("Refunds inserted successfully")
    except Exception as e:
        logging.info(f"Failed to insert refunds into database: {e}")

async def refresh_emag_returns(marketplace: Marketplace):
    # create_database()
    logging.info(f">>>>>>> Refreshing Marketplace : {marketplace.title} <<<<<<<<")

    if marketplace.credentials["type"] == "user_pass":
        
        USERNAME = marketplace.credentials["firstKey"]
        PASSWORD = marketplace.credentials["secondKey"]
        API_KEY = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode('utf-8'))
        
        baseAPIURL = marketplace.baseAPIURL
        endpoint = "/rma"
        read_endpoint = "/read"
        count_endpoint = "/count"

        result = count_all_rmas(baseAPIURL, endpoint, count_endpoint, API_KEY)
        if result:
            pages = result['results']['noOfPages']
            items = result['results']['noOfItems']
            logging.info(f"------------pages--------------{pages}")
            logging.info(f"------------items--------------{items}")
        try:
            current_page  = 1
            while current_page <= int(pages):
                rmas = get_all_rmas(baseAPIURL, endpoint, read_endpoint, API_KEY, current_page)
                logging.info(f">>>>>>> Current Page : {current_page} <<<<<<<<")
                await insert_rmas_into_db(rmas['results'], marketplace.marketplaceDomain)
                current_page += 1
        except Exception as e:
            print('++++++++++++++++++++++++++++++++++++++++++')
            print(e)