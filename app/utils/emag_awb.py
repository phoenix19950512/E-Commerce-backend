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
    'http': 'http://p2p_user:jDkAx4EkAyKw@65.109.7.74:54021',
    'https': 'http://p2p_user:jDkAx4EkAyKw@65.109.7.74:54021',
}

def get_all_awbs(MARKETPLACE_API_URL, ENDPOINT, READ_ENDPOINT,  API_KEY, PROXIES, PUBLIC_KEY=None, usePublicKey=False):
    url = f"{MARKETPLACE_API_URL}{ENDPOINT}/{READ_ENDPOINT}"
    
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

    response = requests.post(url, headers=headers, proxies=PROXIES)
    return response

async def insert_couriers_into_db(couriers, place:str):
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
                account_id,
                account_display_name,
                courier_account_type,
                courier_name,
                courier_account_properties,
                created,
                status,
                market_place
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (account_id, market_place) DO UPDATE SET
                account_display_name = EXCLUDED.account_display_name,
                courier_account_type = EXCLUDED.courier_account_type               
        """).format(sql.Identifier("couriers"))

        for courier in couriers:
            account_id = courier.get('account_id')
            account_display_name = courier.get('account_display_name')
            courier_account_type = courier.get('courier_account_type')
            courier_name = courier.get('courier_name')
            courier_account_properties = json.dumps(courier.get('courier_account_properties'))
            created = courier.get('created')
            status = courier.get('status')
            market_place = place

            value = (
                account_id,
                account_display_name,
                courier_account_type,
                courier_name,
                courier_account_properties,
                created,
                status,
                market_place
            )

            print(value)
            cursor.execute(insert_query, value)
            conn.commit()
        
        cursor.close()
        conn.close()
        print("Couriers inserted successfully")
    except Exception as e:
        print(f"Failed to insert couriers into database: {e}")

async def refresh_emag_awbs(marketplace: Marketplace):
    # create_database()
    logging.info(f">>>>>>> Refreshing Marketplace : {marketplace.title} <<<<<<<<")

    if marketplace.credentials["type"] == "user_pass":
        
        USERNAME = marketplace.credentials["firstKey"]
        PASSWORD = marketplace.credentials["secondKey"]
        API_KEY = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode('utf-8'))
        
        baseAPIURL = marketplace.baseAPIURL
        endpoint = "/awb"
        read_endpoint = "/read"

        result = get_all_awbs(baseAPIURL, endpoint, read_endpoint, API_KEY, PROXIES=PROXIES)
        logging.info(f"#################{result}")
        # await insert_couriers_into_db(result['results'], marketplace.marketplaceDomain)
