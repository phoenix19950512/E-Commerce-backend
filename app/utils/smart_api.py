from psycopg2 import sql
from urllib.parse import urlparse
from app.config import settings
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.internal_product import Internal_Product
from app.models.billing_software import Billing_software
from sqlalchemy import select
import requests
from requests.auth import HTTPBasicAuth
import base64
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PROXIES = {
    'http': 'http://p2p_user:jDkAx4EkAyKw@65.109.7.74:54021',
    'https': 'http://p2p_user:jDkAx4EkAyKw@65.109.7.74:54021',
}

def get_stock(smartbill: Billing_software):
    today = datetime.today()
    today = today.strftime("%Y-%m-%d")

    USERNAME = smartbill.username
    PASSWORD = smartbill.password
    url = "https://ws.smartbill.ro/SBORO/api/stocks"
    params = {
    "cif": smartbill.registration_number,
    "date": today,
    "warehouseName": smartbill.warehouse_name
    }
    credentials = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "accept": "application/json",
    }

    # Replace 'username' and 'password' with the actual credentials
    response = requests.get(url, headers=headers, params=params, proxies=PROXIES)
    # Replace 'username' and 'password' with the actual credentials
    if response.status_code == 200:
        result = response.json()
        products = result.get('list')
        return products
    else:
        return response.json().get('errorText')

async def update_stock(db: AsyncSession):
    results = get_stock()
    for product_list in results:
        products = product_list.get('products')
        for product in products:
            product_code = product.get('productCode')
            result = await db.execute(select(Internal_Product).where(Internal_Product.product_code == product_code))
            db_product = result.scalars.first()
            db_product.stock = product.get('quantity')

def generate_invoice(data):
    USERNAME = "003|5c070dde3f5ed393cf1ff6a610748779"
    PASSWORD = "RO41996145"
    url = "https://ws.smartbill.ro/SBORO/api/invoice"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
    }
    auth = HTTPBasicAuth(USERNAME, PASSWORD)
    response = requests.post(url, headers=headers, json=json.loads(data), auth=auth)
    if response.status_code == 200:
        return response
    else:
        return f"{response.status_code} error, {response.json().get('errorText')}"
