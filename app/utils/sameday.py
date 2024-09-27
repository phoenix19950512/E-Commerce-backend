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
import httpx

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# PROXIES = {
#     'http://': 'http://14a20bb3efda4:d69e723f2d@168.158.127.74:12323',
#     'https://': 'http://14a20bb3efda4:d69e723f2d@168.158.127.74:12323',
# }


async def tracking(awb_barcode):
    api_key = "71a189a2fd4591695fa6b8a2931dac93d6a4f007"
    url = "https://api.sameday.ro/api/client/parcel"
    
    headers = {
        "X-Auth-TOKEN": api_key,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{url}/{awb_barcode}/status-history", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            print("Status Code:", response.status_code)
            print("Error:", response.json())
