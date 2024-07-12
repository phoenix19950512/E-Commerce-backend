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
from app.models.product import Product
from app.schemas.product import ProductCreate
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.database import get_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PROXIES = {
    'http': 'http://p2p_user:jDkAx4EkAyKw@65.109.7.74:54021',
    'https': 'http://p2p_user:jDkAx4EkAyKw@65.109.7.74:54021',
}

def create_database():
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
        logging.info(">>> Created database <<<")
    except Exception as e:
        logging.error(f"Failed to create database: {e}")

def create_products_table(products_table):
    try:
        conn = psycopg2.connect(
            dbname=settings.DB_NAME,
            user=settings.DB_USERNAME,
            password=settings.DB_PASSOWRD,
            host=settings.DB_URL,
            port=settings.DB_PORT
        )

        cursor = conn.cursor()
        create_table_query = sql.SQL("""
            CREATE TABLE IF NOT EXISTS {} (
                id SERIAL PRIMARY KEY,
                admin_user TEXT,
                part_number_key TEXT,
                brand_name TEXT,
                buy_button_rank INTEGER,
                category_id INTEGER,
                brand TEXT,
                name TEXT,
                part_number TEXT,
                sale_price NUMERIC(16, 4),
                currency VARCHAR(10),
                description TEXT,
                url TEXT,
                warranty INTEGER,
                general_stock INTEGER,
                weight NUMERIC(12, 6),
                status INTEGER,
                recommended_price NUMERIC(16, 4),
                images TEXT,
                attachments TEXT,
                vat_id INTEGER,
                family TEXT,
                reversible_vat_charging BOOLEAN,
                min_sale_price NUMERIC(16, 4),
                max_sale_price NUMERIC(16, 4),
                offer_details TEXT,
                availability TEXT,
                stock TEXT,
                handling_time TEXT,
                ean TEXT UNIQUE,
                commission NUMERIC(16, 4),
                validation_status TEXT,
                translation_validation_status TEXT,
                offer_validation_status TEXT,
                auto_translated INTEGER,
                ownership BOOLEAN,
                best_offer_sale_price NUMERIC(16, 4),
                best_offer_recommended_price NUMERIC(16, 4),
                number_of_offers INTEGER,
                genius_eligibility INTEGER,
                recycleWarranties INTEGER
            )
        """).format(sql.Identifier(products_table))

        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(">>> Created table <<<")
    except Exception as e:
        logging.error(f"Failed to create table: {e}")

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


async def insert_products(products, db):
    try:
        for product in products:

            product_model = Product(
                product_name = product.get('name'),
                model_name = product.get('part_number'),
                ean = product.get('ean')[0] if product.get('ean') else None,
                price = product.get('sale_price'),
                image_link = product.get('images')[0]['url'] if product.get('images') else None,
                barcode_title = product.get('part_number_key'),
                masterbox_title = product.get('brand_name'),
                link_address_1688 = product.get('url'),
                price_1688 = 0,  # Map appropriately if available
                variation_name_1688 = product.get('brand'),
                pcs_ctn = "",  # Map appropriately if available
                weight = product.get('weight'),
                volumetric_weight = 0,  # Map appropriately if available
                dimensions = "",  # Map appropriately if available
                supplier_id = 1,  # Map appropriately if available
                english_name = "",  # Map appropriately if available
                romanian_name = "", # Map appropriately if available
                material_name_en = "",  # Map appropriately if available
                material_name_ro = "",  # Map appropriately if available
                hs_code = "",  # Map appropriately if available
                battery = False,  # Map appropriately if available
                default_usage = "",  # Map appropriately if available
                production_time = 0.0,  # Map appropriately if available
                discontinued = False,  # Map appropriately if available
                stock = product.get('stock')[0]['value'] if product.get('stock') else None,
                internal_shipping_price = 0  # Map appropriately if available
            )

            stmt = insert(Product).values(
                product_name=product_model.product_name,
                model_name=product_model.model_name,
                ean=product_model.ean,
                price=product_model.price,
                image_link=product_model.image_link,
                barcode_title=product_model.barcode_title,
                masterbox_title=product_model.masterbox_title,
                link_address_1688=product_model.link_address_1688,
                price_1688=product_model.price_1688,
                variation_name_1688=product_model.variation_name_1688,
                pcs_ctn=product_model.pcs_ctn,
                weight=product_model.weight,
                volumetric_weight=product_model.volumetric_weight,
                dimensions=product_model.dimensions,
                supplier_id=product_model.supplier_id,
                english_name=product_model.english_name,
                romanian_name=product_model.romanian_name,
                material_name_en=product_model.material_name_en,
                material_name_ro=product_model.material_name_ro,
                hs_code=product_model.hs_code,
                battery=product_model.battery,
                default_usage=product_model.default_usage,
                production_time=product_model.production_time,
                discontinued=product_model.discontinued,
                stock=product_model.stock,
                internal_shipping_price=product_model.internal_shipping_price
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=['ean'],
                set_={
                    'product_name': stmt.excluded.product_name,
                    'model_name': stmt.excluded.model_name,
                    'price': stmt.excluded.price,
                    'image_link': stmt.excluded.image_link,
                    'barcode_title': stmt.excluded.barcode_title,
                    'masterbox_title': stmt.excluded.masterbox_title,
                    'link_address_1688': stmt.excluded.link_address_1688,
                    'price_1688': stmt.excluded.price_1688,
                    'variation_name_1688': stmt.excluded.variation_name_1688,
                    'pcs_ctn': stmt.excluded.pcs_ctn,
                    'weight': stmt.excluded.weight,
                    'volumetric_weight': stmt.excluded.volumetric_weight,
                    'dimensions': stmt.excluded.dimensions,
                    'supplier_id': stmt.excluded.supplier_id,
                    'english_name': stmt.excluded.english_name,
                    'romanian_name': stmt.excluded.romanian_name,
                    'material_name_en': stmt.excluded.material_name_en,
                    'material_name_ro': stmt.excluded.material_name_ro,
                    'hs_code': stmt.excluded.hs_code,
                    'battery': stmt.excluded.battery,
                    'default_usage': stmt.excluded.default_usage,
                    'production_time': stmt.excluded.production_time,
                    'discontinued': stmt.excluded.discontinued,
                    'stock': stmt.excluded.stock,
                    'internal_shipping_price': stmt.excluded.internal_shipping_price
                }
            )

            await db.execute(stmt)
        
        await db.commit()
        logging.info("Products inserted successfully into the 'products' table")
    except Exception as e:
        # db.rollback()
        logging.error(f"Failed to insert products into the 'products' table: {e}")


async def insert_products_into_db(products, username, products_table):
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
                admin_user,
                part_number_key,
                brand_name,
                buy_button_rank,
                category_id,
                brand,
                name,
                part_number,
                sale_price,
                currency,
                description,
                url,
                warranty,
                general_stock,
                weight,
                status,
                recommended_price,
                images,
                attachments,
                vat_id,
                family,
                reversible_vat_charging,
                min_sale_price,
                max_sale_price,
                offer_details,
                availability,
                stock,
                handling_time,
                ean,
                commission,
                validation_status,
                translation_validation_status,
                offer_validation_status,
                auto_translated,
                ownership,
                best_offer_sale_price,
                best_offer_recommended_price,
                number_of_offers,
                genius_eligibility,
                recycleWarranties
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (id) DO UPDATE SET
                part_number_key = EXCLUDED.part_number_key,
                admin_user = EXCLUDED.admin_user,
                brand_name = EXCLUDED.brand_name,
                buy_button_rank = EXCLUDED.buy_button_rank,
                category_id = EXCLUDED.category_id,
                brand = EXCLUDED.brand,
                name = EXCLUDED.name,
                part_number = EXCLUDED.part_number,
                sale_price = EXCLUDED.sale_price,
                currency = EXCLUDED.currency,
                description = EXCLUDED.description,
                url = EXCLUDED.url,
                warranty = EXCLUDED.warranty,
                general_stock = EXCLUDED.general_stock,
                weight = EXCLUDED.weight,
                status = EXCLUDED.status,
                recommended_price = EXCLUDED.recommended_price,
                images = EXCLUDED.images,
                attachments = EXCLUDED.attachments,
                vat_id = EXCLUDED.vat_id,
                family = EXCLUDED.family,
                reversible_vat_charging = EXCLUDED.reversible_vat_charging,
                min_sale_price = EXCLUDED.min_sale_price,
                max_sale_price = EXCLUDED.max_sale_price,
                offer_details = EXCLUDED.offer_details,
                availability = EXCLUDED.availability,
                stock = EXCLUDED.stock,
                handling_time = EXCLUDED.handling_time,
                ean = EXCLUDED.ean,
                commission = EXCLUDED.commission,
                validation_status = EXCLUDED.validation_status,
                translation_validation_status = EXCLUDED.translation_validation_status,
                offer_validation_status = EXCLUDED.offer_validation_status,
                auto_translated = EXCLUDED.auto_translated,
                ownership = EXCLUDED.ownership,
                best_offer_sale_price = EXCLUDED.best_offer_sale_price,
                best_offer_recommended_price = EXCLUDED.best_offer_recommended_price,
                number_of_offers = EXCLUDED.number_of_offers,
                genius_eligibility = EXCLUDED.genius_eligibility,
                recycleWarranties = EXCLUDED.recycleWarranties
        """).format(sql.Identifier(products_table))

        for product in products:
            
            id = product.get('id')
            part_number_key = product.get('part_number_key')
            brand_name = product.get('brand_name')
            buy_button_rank = product.get('buy_button_rank')
            category_id = product.get('category_id')
            brand = product.get('brand')
            name = product.get('name')
            part_number = product.get('part_number')
            sale_price = product.get('sale_price')
            currency = product.get('currency')
            description = product.get('description')
            url = product.get('url')
            warranty = product.get('warranty')
            general_stock = product.get('general_stock')
            weight = product.get('weight')
            status = product.get('status')
            recommended_price = product.get('recommended_price', "")
            images = product.get('images', [])
            attachments = product.get('attachments', [])
            vat_id = product.get('vat_id')
            family = product.get('family', {})
            reversible_vat_charging = product.get('reversible_vat_charging')
            min_sale_price = product.get('min_sale_price')
            max_sale_price = product.get('max_sale_price')
            offer_details = product.get('offer_details', {})
            availability = product.get('availability', [])
            stock = product.get('stock', [])
            handling_time = product.get('handling_time', [])
            ean = product.get('ean', [])
            commission = product.get('commission')
            validation_status = product.get('validation_status', [])
            translation_validation_status = product.get('translation_validation_status', [])
            offer_validation_status = product.get('offer_validation_status', {})
            auto_translated = product.get('auto_translated')
            ownership = product.get('ownership')
            best_offer_sale_price = product.get('best_offer_sale_price')
            best_offer_recommended_price = product.get('best_offer_recommended_price')
            number_of_offers = product.get('number_of_offers')
            genius_eligibility = product.get('genius_eligibility')
            recycleWarranties = product.get('recycleWarranties')

            images_json = json.dumps(images)
            attachments_json = json.dumps(attachments)
            family_json = json.dumps(family)
            offer_details_json = json.dumps(offer_details)
            availability_json = json.dumps(availability)
            stock_json = json.dumps(stock)
            handling_time_json = json.dumps(handling_time)
            ean_json = json.dumps(ean)
            validation_status_json = json.dumps(validation_status)
            translation_validation_status_json = json.dumps(translation_validation_status)
            offer_validation_status_json = json.dumps(offer_validation_status)
            # if len(images) > 0:
            #     parsed_url = urlparse(images[0]["url"])
            #     path = parsed_url.path
            #     local_directory = f".{os.path.dirname(path)}"
            #     local_file_path = f".{path}"
            #     os.makedirs(local_directory, exist_ok=True)
            #     try:
            #         response = requests.get(images[0]["url"])
            #         response.raise_for_status()
            #         with open(local_file_path, "wb") as file:
            #             file.write(response.content)
            #         print(f"Image downloaded successfully to {local_file_path}.")
            #     except requests.RequestException as e:
            #         print(f"Failed to download image. Error: {e}")
            cursor.execute(insert_query, (
                id,
                username,
                part_number_key,
                brand_name,
                buy_button_rank,
                category_id,
                brand,
                name,
                part_number,
                sale_price,
                currency,
                description,
                url,
                warranty,
                general_stock,
                weight,
                status,
                recommended_price,
                images_json,
                attachments_json,
                vat_id,
                family_json,
                reversible_vat_charging,
                min_sale_price,
                max_sale_price,
                offer_details_json,
                availability_json,
                stock_json,
                handling_time_json,
                ean_json,
                commission,
                validation_status_json,
                translation_validation_status_json,
                offer_validation_status_json,
                auto_translated,
                ownership,
                best_offer_sale_price,
                best_offer_recommended_price,
                number_of_offers,
                genius_eligibility,
                recycleWarranties,
            ))
            conn.commit()
        
        cursor.close()
        conn.close()
        print("Products inserted successfully")
    except Exception as e:
        print(f"Failed to insert products into database: {e}")

async def get_signature(public_key, private_key, page_nr=1, items_per_page=100):
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
    logging.info(signature)
    return signature

async def refresh_products(marketplace: Marketplace, db: AsyncSession):
    # create_database()
    logging.info(f">>>>>>> Refreshing Marketplace : {marketplace.title} <<<<<<<<")

    products_table = f"{marketplace.marketplaceDomain.replace('.', '_')}_products"
    create_products_table(products_table)

    if marketplace.credentials["type"] == "user_pass":
        
        USERNAME = marketplace.credentials["firstKey"]
        PASSWORD = marketplace.credentials["secondKey"]
        API_KEY = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode('utf-8'))
        result = count_all_products(marketplace.baseAPIURL, marketplace.products_crud["endpoint"], marketplace.products_crud["count"], API_KEY)
        if result:
            pages = result['results']['noOfPages']
            items = result['results']['noOfItems']

            currentPage = 1
            baseAPIURL = marketplace.baseAPIURL
            endpoint = marketplace.products_crud['endpoint']
            read_endpoint = marketplace.products_crud['read']
            try:
                while currentPage <= int(pages):
                    products = get_all_products(baseAPIURL, endpoint, read_endpoint, API_KEY, currentPage)
                    logging.info(f">>>>>>> Current Page : {currentPage} <<<<<<<<")
                    if products and not products.get('isError'):
                        async with db as session:
                            await insert_products_into_db(products['results'], USERNAME, products_table)
                            await insert_products(products['results'], session)
                    currentPage += 1
            except Exception as e:
                print('++++++++++++++++++++++++++++++++++++++++++')
                print(e)
    elif marketplace.credentials["type"] == "pub_priv":
        PUBLIC_KEY = marketplace.credentials["firstKey"]
        PRIVATE_KEY = marketplace.credentials["secondKey"]
        logging.info("starting count")
        sign = get_signature(PUBLIC_KEY, PRIVATE_KEY)
        result = count_all_products(marketplace.baseAPIURL, marketplace.products_crud["endpoint"], marketplace.products_crud["count"], sign, PUBLIC_KEY, True, proxies=PROXIES)
        if result:
            pages = result['results']['noOfPages']
            currentPage = 1
            while currentPage <= pages:
                products = get_all_products(marketplace.baseAPIURL, marketplace.products_crud["endpoint"], marketplace.products_crud["read"], sign, currentPage, PUBLIC_KEY, True, proxies=PROXIES)
                if products and not products['isError']:
                    insert_products_into_db(products['results'], PUBLIC_KEY, products_table)
                    currentPage += 1



