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

def count_all_awbs(MARKETPLACE_API_URL, PRODUCTS_ENDPOINT, COUNT_ENGPOINT, API_KEY, PUBLIC_KEY=None, usePublicKey=False):
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

    response = requests.post(url, headers=headers, proxies=PROXIES)
    if response.status_code == 200:
        logging.info("success counting awbs")
        return response.json()
    else:
        logging.error(f"Failed to retrieve products: {response.status_code}")
        return None

def save(MARKETPLACE_API_URL, PRODUCTS_ENDPOINT, READ_ENDPOINT,  API_KEY, data, PUBLIC_KEY=None, usePublicKey=False):
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

    response = requests.post(url, data=data, headers=headers, proxies=PROXIES)
    if response.status_code == 200:
        products = response.json()
        return products
    else:
        logging.info(f"Failed to retrieve products: {response.status_code}")
        return None

async def refresh_awb(marketplace: Marketplace, db: AsyncSession):
    if marketplace.credentials["type"] == "user_pass":
        
        USERNAME = marketplace.credentials["firstKey"]
        PASSWORD = marketplace.credentials["secondKey"]
        API_KEY = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode('utf-8'))
        result = count_all_awbs(marketplace.baseAPIURL, "/awb", "/read", API_KEY)
        print(result)
        if result:
            pages = result['results']
            items = result['results']['noOfItems']

            print("------------pages--------------", pages)
            print("------------items--------------", items)
            currentPage = 1
            baseAPIURL = marketplace.baseAPIURL
            endpoint = marketplace.products_crud['endpoint']
            read_endpoint = marketplace.products_crud['read']


async def save_awb(marketplace: Marketplace, data, db: AsyncSession):
    if marketplace.credentials["type"] == "user_pass":
        
        USERNAME = marketplace.credentials["firstKey"]
        PASSWORD = marketplace.credentials["secondKey"]
        API_KEY = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode('utf-8'))
        result = save(marketplace.baseAPIURL, "/awb", "/save", API_KEY, data)
        print(result)
        return result['results']
