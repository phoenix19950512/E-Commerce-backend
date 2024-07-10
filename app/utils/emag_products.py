from psycopg2 import sql
from urllib.parse import urlparse
from app.config import settings
import requests
import psycopg2
import base64
import urllib
import hashlib
import json
import os
import time


PROXIES = {
    'http': 'http://14a20bb3efda4:d69e723f2d@89.42.81.197:12323',
    'https': 'http://14a20bb3efda4:d69e723f2d@89.42.81.197:12323',
}

def create_database(dbinfo):
    try:
        conn = psycopg2.connect(
            dbname=settings.DB_NAME,
            user=settings.DB_USERNAME,
            password=settings.DB_PASSOWRD,
            host=settings.DB_URL,
            port=settings.DB_PORT
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{settings.DB_NAME}'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(settings.DB_NAME)))
        cursor.close()
        conn.close()
        print(">>> Created database <<<")
    except Exception as e:
        print(f"Failed to create database: {e}")

def create_products_table():
    try:
        conn = psycopg2.connect(
            dbname=settings.DB_NAME,
            user=settings.DB_USERNAME,
            password=settings.DB_PASSOWRD,
            host=settings.DB_URL,
            port=settings.DB_PORT
        )
        cursor = conn.cursor()
        create_table_query = """
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                 product_name TEXT,
                model_name TEXT,
                sku TEXT,
                price NUMERIC(16, 4),
                image_link TEXT,
                barcode_title TEXT,
                masterbox_title TEXT,
                link_address_1688 TEXT,
                price_1688 NUMERIC(16, 4),
                variation_name_1688 TEXT,
                pcs_ctn TEXT,
                weight NUMERIC(12, 6),
                volumetric_weight NUMERIC(12, 6),
                dimensions TEXT,
                supplier_id INTEGER,
                english_name TEXT,
                romanian_name TEXT,
                material_name_en TEXT,
                material_name_ro TEXT,
                hs_code TEXT,
                battery BOOLEAN,
                default_usage TEXT,
                production_time NUMERIC(16, 4),
                discontinued BOOLEAN,
                stock INTEGER,
                internal_shipping_price NUMERIC(16, 4)
            )
        """
        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
        conn.close()
        print(">>> Created table <<<")
    except Exception as e:
        print(f"Failed to create table: {e}")

def create_product(MARKETPLACE_API_URL, API_KEY, product_data, PUBLIC_KEY=None, usePublicKey=False):
    url = f"{MARKETPLACE_API_URL}/product_offer/save"
    
    if usePublicKey:
        headers = {
            "X-Request-Public-Key": f"{PUBLIC_KEY}",
            "X-Request-Signature": f"{API_KEY}"
        }
    else:
        api_key = str(API_KEY).replace("b'", '').replace("'", "")
        headers = {
            "Authorization": f"Basic {api_key}",
            "Content-Type": "application/json"
        }
    
    response = requests.post(url, json=product_data, headers=headers, proxies=PROXIES)
    
    if response.status_code == 200:
        print("Product created successfully")
        return response.json()
    else:
        print(f"Failed to create product: {response.status_code}")
        print(response.text)
        return None

def count_all_products(MARKETPLACE_API_URL, PRODUCTS_ENDPOINT, COUNT_ENGPOINT, API_KEY, PUBLIC_KEY=None, usePublicKey=False):
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
        return response.json()
    else:
        print(f"Failed to retrieve products: {response.status_code}")
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
        print(f"Failed to retrieve products: {response.status_code}")
        return None

def insert_products_into_db(products, username):
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
            INSERT INTO products (
                id,
                product_name,
                model_name,
                sku,
                price,
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
                internal_shipping_price
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (id) DO UPDATE SET
                product_name = EXCLUDED.product_name,
                model_name = EXCLUDED.model_name,
                sku = EXCLUDED.sku,
                price = EXCLUDED.price,
                image_link = EXCLUDED.image_link,
                barcode_title = EXCLUDED.barcode_title,
                masterbox_title = EXCLUDED.masterbox_title,
                link_address_1688 = EXCLUDED.link_address_1688,
                price_1688 = EXCLUDED.price_1688,
                variation_name_1688 = EXCLUDED.variation_name_1688,
                pcs_ctn = EXCLUDED.pcs_ctn,
                weight = EXCLUDED.weight,
                volumetric_weight = EXCLUDED.volumetric_weight,
                dimensions = EXCLUDED.dimensions,
                supplier_id = EXCLUDED.supplier_id,
                english_name = EXCLUDED.english_name,
                romanian_name = EXCLUDED.romanian_name,
                material_name_en = EXCLUDED.material_name_en,
                material_name_ro = EXCLUDED.material_name_ro,
                hs_code = EXCLUDED.hs_code,
                battery = EXCLUDED.battery,
                default_usage = EXCLUDED.default_usage,
                production_time = EXCLUDED.production_time,
                discontinued = EXCLUDED.discontinued,
                stock = EXCLUDED.stock
                internal_shipping_price = EXCLUDED.internal_shipping_price
        """)

        for product in products:
            cursor.execute(insert_query, (
                product.get('id'),
                product.get('product_name'),
                product.get('model_name'),
                product.get('sku'),
                product.get('price'),
                product.get('image_link'),
                product.get('barcode_title'),
                product.get('masterbox_title'),
                product.get('link_address_1688'),
                product.get('price_1688'),
                product.get('variation_name_1688'),
                product.get('pcs_ctn'),
                product.get('weight'),
                product.get('volumetric_weight'),
                product.get('dimensions'),
                product.get('supplier_id'),
                product.get('english_name'),
                product.get('romanian_name'),
                product.get('material_name_en'),
                product.get('material_name_ro'),
                product.get('hs_code'),
                product.get('battery'),
                product.get('default_usage'),
                product.get('production_time'),
                product.get('discontinued'),
                product.get('stock'),
                product.get('internal_shipping_price')
            ))
            conn.commit()
        
        cursor.close()
        conn.close()
        print("Products inserted successfully")
    except Exception as e:
        print(f"Failed to insert products into database: {e}")

def get_signature(public_key, private_key, page_nr=1, items_per_page=100):
    request_params = {
        'page_nr': page_nr,
        'items_per_page': items_per_page
    }
    url_query_string = urllib.parse.urlencode(
        request_params,
        safe='|',
        quote_via=urllib.parse.quote
    )
    current_timestamp = int(time.time())
    remainder = current_timestamp % 10000
    time_digits = str(remainder).zfill(4)
    # current_time = str(int(time.time()))
    # time_digits = current_time[-4:]
    string_to_hash = ( public_key + '||' + hashlib.sha512(private_key.encode()).hexdigest() + '||' + url_query_string + '||' + time_digits )
    hash_value = hashlib.sha512(string_to_hash.encode()).hexdigest().lower()
    signature = time_digits + hash_value
    print(signature)
    return signature

def refresh_products(marketplace):
    # create_database()
    print(f">>>>>>> Refreshing Marketplace : {marketplace.title} <<<<<<<<")
    create_products_table()
    if marketplace.credentials["type"] == "user_pass":
        USERNAME = marketplace.credentials["firstKey"]
        PASSWORD = marketplace.credentials["secondKey"]
        API_KEY = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode('utf-8'))
        result = count_all_products(marketplace.baseAPIURL, marketplace.products_crud["endpoint"], marketplace.products_crud["count"], API_KEY, proxies=PROXIES)
        if result:
            pages = result['results']['noOfPages']
            currentPage = 1
            while currentPage < int(pages) + 1:
                products = get_all_products(marketplace.baseAPIURL, marketplace.products_crud["endpoint"], marketplace.products_crud["count"], API_KEY, currentPage, proxies=PROXIES)
                if products and not products['isError']:
                    insert_products_into_db(products['results'], USERNAME)
                    currentPage += 1
    elif marketplace.credentials["type"] == "pub_priv":
        PUBLIC_KEY = marketplace.credentials["firstKey"]
        PRIVATE_KEY = marketplace.credentials["secondKey"]
        sign = get_signature(PUBLIC_KEY, PRIVATE_KEY)
        result = count_all_products(marketplace.baseAPIURL, marketplace.products_crud["endpoint"], marketplace.products_crud["count"], sign, PUBLIC_KEY, True, proxies=PROXIES)
        if result:
            pages = result['results']['noOfPages']
            currentPage = 1
            while currentPage <= pages:
                products = get_all_products(marketplace.baseAPIURL, marketplace.products_crud["endpoint"], marketplace.products_crud["count"], sign, currentPage, PUBLIC_KEY, True, proxies=PROXIES)
                if products and not products['isError']:
                    insert_products_into_db(products['results'], PUBLIC_KEY)
                    currentPage += 1