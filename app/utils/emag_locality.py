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

def get_all_localities(MARKETPLACE_API_URL, Localities_ENDPOINT, READ_ENDPOINT,  API_KEY, currentPage, PROXIES, PUBLIC_KEY=None, usePublicKey=False):
    url = f"{MARKETPLACE_API_URL}{Localities_ENDPOINT}/{READ_ENDPOINT}"
    
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
        localities = response.json()
        return localities
    else:
        logging.info(f"Failed to retrieve refunds: {response.status_code}")
        return None

def count_all_localities(MARKETPLACE_API_URL, Localities_ENDPOINT, COUNT_ENGPOINT, API_KEY, PROXIES, PUBLIC_KEY=None, usePublicKey=False):
    logging.info("counting start")
    url = f"{MARKETPLACE_API_URL}{Localities_ENDPOINT}/{COUNT_ENGPOINT}"
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
        logging.info("success localities count")
        return response.json()
    else:
        logging.error(f"Failed to retrieve localities: {response.status_code}")
        return None

async def insert_localities_into_db(localities, place:str):
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
                name,
                name_latin,
                region1,
                region2,
                region3,
                region1_latin,
                region2_latin,
                region3_latin,
                geoid,
                modified,
                zipcode,
                country_code,
                localtity_marketplace
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (id, localtity_marketplace) DO UPDATE SET
                name = EXCLUDED.name,
                name_latin = EXCLUDED.name_latin               
        """).format(sql.Identifier("localities"))

        for locality in localities:
            id = locality.get('emag_id')
            name = locality.get('name')
            name_latin = locality.get('name_latin')
            region1 = locality.get('region1')
            region2 = locality.get('region2')
            region3 = locality.get('region3')
            region1_latin = locality.get('region1_latin')
            region2_latin = locality.get('region2_latin')
            region3_latin = locality.get('region3_latin')
            geoid = locality.get('geoid')
            modified = locality.get('modified')
            zipcode = locality.get('zipcode')
            country_code = locality.get('country_code')
            localtity_marketplace = place

            value = (
                id,
                name,
                name_latin,
                region1,
                region2,
                region3,
                region1_latin,
                region2_latin,
                region3_latin,
                geoid,
                modified,
                zipcode,
                country_code,
                localtity_marketplace
            )
            cursor.execute(insert_query, value)
            conn.commit()
        
        cursor.close()
        conn.close()
        print("Localities inserted successfully")
    except Exception as e:
        print(f"Failed to insert localities into database: {e}")

async def refresh_localities(marketplace: Marketplace):
    # create_database()
    logging.info(f">>>>>>> Refreshing Marketplace : {marketplace.title} <<<<<<<<")

    if marketplace.credentials["type"] == "user_pass":
        
        USERNAME = marketplace.credentials["firstKey"]
        PASSWORD = marketplace.credentials["secondKey"]
        API_KEY = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode('utf-8'))
        
        baseAPIURL = marketplace.baseAPIURL
        endpoint = "/locality"
        read_endpoint = "/read"
        count_endpoint = "/count"

        # result = get_attachments(API_KEY, PROXIES)
        # print(result)

        result = count_all_localities(baseAPIURL, endpoint, count_endpoint, API_KEY, PROXIES=PROXIES)
        if result:
            pages = result['results']['noOfPages']
            items = result['results']['noOfItems']
            print("------------pages--------------", pages)
            print("------------items--------------", items)
        try:
            current_page  = 1
            while current_page <= int(pages):
                localities = get_all_localities(baseAPIURL, endpoint, read_endpoint, API_KEY, current_page, PROXIES=PROXIES)
                logging.info(f">>>>>>> Current Page : {current_page} <<<<<<<<")
                if len(localities['results'] ) == 0:
                    print("empty locality")
                    break
                await insert_localities_into_db(localities['results'], marketplace.marketplaceDomain)
                current_page += 1
        except Exception as e:
            print('++++++++++++++++++++++++++++++++++++++++++')
            print(e)