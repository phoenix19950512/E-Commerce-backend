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
    'http': 'http://14a20bb3efda4:d69e723f2d@168.158.127.74:12323',
    'https': 'http://14a20bb3efda4:d69e723f2d@168.158.127.74:12323',
}


def tracking(awb_number):
    api_key = "84722802fc63bd2ebc424e18acfb5a55b77db096"
    url = "https://api.sameday.ro/api/client/awb"
    
    headers = {
        "X-Auth-TOKEN": f"{api_key}",
    }

    response = requests.get(f"{url}/{awb_number}/status?_format=json", headers=headers, proxies=PROXIES)
    if response.status_code == 200:
        result = response.json()
        return result.get('expeditionStatus').get('statusId')
    else:
        print("Status Code:", response.status_code)
        print("Error:", response.json())
