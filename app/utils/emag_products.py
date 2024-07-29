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
                id INTEGER,
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
                ean TEXT PRIMARY KEY UNIQUE,
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
                recycleWarranties INTEGER,
                market_place TEXT
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


async def insert_products(products, mp_name: str):
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
                part_number_key,
                product_name,
                model_name,
                buy_button_rank,
                price,
                sale_price,
                ean,
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
                warehouse,
                internal_shipping_price,
                market_place
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (ean) DO UPDATE SET
                buy_button_rank = EXCLUDED.buy_button_rank,
                stock = EXCLUDED.stock,
                market_place = array(SELECT DISTINCT unnest(array_cat(EXCLUDED.market_place, internal_products.market_place)))
        """).format(sql.Identifier("internal_products"))

        for product in products:
            id = product.get('id')
            part_number_key = product.get('part_number_key')
            product_name = product.get('name')
            model_name = product.get('brand')
            buy_button_rank = product.get('buy_button_rank')
            price = 0
            sale_price = Decimal(product.get('sale_price', '0.0'))
            ean = str(product.get('ean')[0]) if product.get('ean') else None
            image_link = product.get('images')[0]['url'] if product.get('images') else None
            barcode_title = ""
            masterbox_title = ""
            link_address_1688 = ""
            price_1688 = Decimal('0')
            variation_name_1688 = ""
            pcs_ctn = ""
            weight_value = product.get('weight')
            if isinstance(weight_value, str):
                weight_value = weight_value.replace(',', '.')  # Handle any comma as decimal separator
            weight = Decimal(weight_value) if weight_value else Decimal('0')
            volumetric_weight = 0
            dimensions = ""
            supplier_id = 0
            english_name = ""
            romanian_name = ""
            material_name_en = ""
            material_name_ro = ""
            hs_code = ""
            battery = False
            default_usage = ""
            production_time = Decimal('0')
            discontinued = False
            stock = int(product.get('stock')[0].get('value') if product.get('stock') else 0)
            warehouse = ""
            internal_shipping_price = Decimal('0')
            market_place = [mp_name]  # Ensure this is an array to use array_cat

            values = (
                id,
                part_number_key,
                product_name,
                model_name,
                buy_button_rank,
                price,
                sale_price,
                ean,
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
                warehouse,
                internal_shipping_price,
                market_place
            )

            cursor.execute(insert_query, values)
            conn.commit()
        
        cursor.close()
        conn.close()
        print("$$$$$$$$$$$$Products inserted into Products successfully")
    except Exception as e:
        print(f"$$$$$$$$$$$$$Failed to insert products into database: {e}")


async def insert_products_into_db(products, username, place):
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
                recycleWarranties,
                market_place
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (ean) DO UPDATE SET
                sale_price = EXCLUDED.sale_price,
                stock = EXCLUDED.stock
        """).format(sql.Identifier("products"))

        for product in products:
            id = product.get('id')
            part_number_key = product.get('part_number_key')
            brand_name = product.get('brand_name')
            buy_button_rank = product.get('buy_button_rank')
            category_id = product.get('category_id')
            brand = product.get('brand')
            name = product.get('name')
            part_number = product.get('part_number')
            sale_price = Decimal(product.get('sale_price', '0.0'))
            currency = product.get('currency')
            description = product.get('description')
            url = product.get('url')
            warranty = product.get('warranty')
            general_stock = product.get('general_stock')
            weight = product.get('weight')
            status = product.get('status')
            recommended_price = product.get('recommended_price', "")
            images = product.get('images')[0]['url'] if product.get('images') else None
            attachments = product.get('attachments', [])
            vat_id = product.get('vat_id')
            family = product.get('family', {})
            reversible_vat_charging = product.get('reversible_vat_charging')
            min_sale_price = product.get('min_sale_price')
            max_sale_price = product.get('max_sale_price')
            offer_details = product.get('offer_details', {})
            availability = product.get('availability', [])
            stock = sum(product.get('stock', []))
            handling_time = product.get('handling_time', [])
            ean = product.get('ean')[0] if product.get('ean') else None
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
            market_place = place

            attachments_json = json.dumps(attachments)
            family_json = json.dumps(family)
            offer_details_json = json.dumps(offer_details)
            availability_json = json.dumps(availability)
            handling_time_json = json.dumps(handling_time)
            validation_status_json = json.dumps(validation_status)
            translation_validation_status_json = json.dumps(translation_validation_status)
            offer_validation_status_json = json.dumps(offer_validation_status)

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
                images,
                attachments_json,
                vat_id,
                family_json,
                reversible_vat_charging,
                min_sale_price,
                max_sale_price,
                offer_details_json,
                availability_json,
                stock,
                handling_time_json,
                ean,
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
                market_place
            ))
            conn.commit()
        
        cursor.close()
        conn.close()
        print("Products inserted successfully")
    except Exception as e:
        print(f"Failed to insert products into database: {e}")

async def refresh_products(marketplace: Marketplace, db: AsyncSession):
    # create_database()
    logging.info(f">>>>>>> Refreshing Marketplace : {marketplace.title} <<<<<<<<")

    if marketplace.credentials["type"] == "user_pass":
        
        USERNAME = marketplace.credentials["firstKey"]
        PASSWORD = marketplace.credentials["secondKey"]
        API_KEY = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode('utf-8'))
        result = count_all_products(marketplace.baseAPIURL, marketplace.products_crud["endpoint"], marketplace.products_crud["count"], API_KEY)
        if result:
            pages = result['results']['noOfPages']
            items = result['results']['noOfItems']

            print("------------pages--------------", pages)
            print("------------items--------------", items)
            currentPage = 1
            baseAPIURL = marketplace.baseAPIURL
            endpoint = marketplace.products_crud['endpoint']
            read_endpoint = marketplace.products_crud['read']
            try:
                while currentPage <= int(pages):
                    products = get_all_products(baseAPIURL, endpoint, read_endpoint, API_KEY, currentPage)

                    logging.info(f">>>>>>> Current Page : {currentPage} <<<<<<<<")
                    if products and not products.get('isError'):
                        await insert_products_into_db(products['results'], USERNAME, marketplace.marketplaceDomain)
                        await insert_products(products['results'], marketplace.marketplaceDomain)
                    currentPage += 1
            except Exception as e:
                print('++++++++++++++++++++++++++++++++++++++++++')
                print(e)
    elif marketplace.credentials["type"] == "pub_priv":
        PUBLIC_KEY = marketplace.credentials["firstKey"]
        PRIVATE_KEY = marketplace.credentials["secondKey"]
        logging.info("starting count")
        result = count_all_products(marketplace.baseAPIURL, marketplace.products_crud["endpoint"], marketplace.products_crud["count"], sign, PUBLIC_KEY, True, proxies=PROXIES)
        if result:
            pages = result['results']['noOfPages']
            currentPage = 1
            while currentPage <= pages:
                products = get_all_products(marketplace.baseAPIURL, marketplace.products_crud["endpoint"], marketplace.products_crud["read"], sign, currentPage, PUBLIC_KEY, True, proxies=PROXIES)
                if products and not products['isError']:
                    insert_products_into_db(products['results'], PUBLIC_KEY, products_table)
                    currentPage += 1
