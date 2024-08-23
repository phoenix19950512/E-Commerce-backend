from psycopg2 import sql
from urllib.parse import urlparse
from app.config import settings
from fastapi import Depends
import requests
from requests.auth import HTTPBasicAuth
import base64
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# PROXIES = {
#     'http': 'http://p2p_user:jDkAx4EkAyKw@65.109.7.74:54021',
#     'https': 'http://p2p_user:jDkAx4EkAyKw@65.109.7.74:54021',
# }

def get_stock():
    USERNAME = "003|5c070dde3f5ed393cf1ff6a610748779"
    PASSWORD = "RO41996145"
    url = "https://ws.smartbill.ro/SBORO/api/stocks"
    headers = {
    "accept": "application/json",
    }

    # Replace 'username' and 'password' with the actual credentials
    auth = HTTPBasicAuth(USERNAME, PASSWORD)
    response = requests.get(url, headers=headers, auth=auth)
    if response.status_code == 200:
        return response.json()
    else:
        return f"{response.status_code} error, {response.json().get('errorText')}"

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
