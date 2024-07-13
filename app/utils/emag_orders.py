import requests
import psycopg2
import base64
import json
import os
from app.config import settings
from psycopg2 import sql
from urllib.parse import urlparse
from app.models.marketplace import Marketplace
from app.models.orders import Order
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from sqlalchemy.exc import IntegrityError
import logging
from sqlalchemy import insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


MARKETPLACE_URL = 'https://marketplace.emag.ro/'
MARKETPLACE_API_URL = 'https://marketplace-api.emag.ro/api-3'
ORDERS_ENDPOINT = "/order"

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
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE {} WITH ENCODING 'UTF8'").format(sql.Identifier(DB_NAME)))
        cursor.close()
        conn.close()
        print(">>> Created database <<<")
    except Exception as e:
        print(f"Failed to create database: {e}")

def create_customers_table(customer_table):
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
                id serial PRIMARY KEY,
                mkt_id BIGINT,
                name TEXT,
                company TEXT,
                gender TEXT,
                phone_1 TEXT,
                phone_2 TEXT,
                phone_3 TEXT,
                registration_number TEXT,
                code TEXT,
                email TEXT,
                billing_name TEXT,
                billing_phone TEXT,
                billing_country TEXT,
                billing_suburb TEXT,
                billing_city TEXT,
                billing_locality_id TEXT,
                billing_street TEXT,
                billing_postal_code TEXT,
                shipping_country TEXT,
                shipping_suburb TEXT,
                shipping_city TEXT,
                shipping_locality_id TEXT,
                shipping_postal_code TEXT,
                shipping_contact TEXT,
                shipping_phone TEXT,
                created TIMESTAMP,
                modified TIMESTAMP,
                bank TEXT,
                iban TEXT,
                legal_entity INT,
                fax TEXT,
                is_vat_payer INT,
                liable_person TEXT,
                shipping_street TEXT
            )"""
        ).format(sql.Identifier(customer_table))
        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(">>> Created customer table <<<")
    except Exception as e:
        logging.info(f"Failed to create table: {e}")

def create_orders_table(orders_table):
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
                id BIGINT PRIMARY KEY,
                vendor_name TEXT,
                type INT,
                parent_id BIGINT,
                date TIMESTAMP,
                payment_mode VARCHAR(50),
                detailed_payment_method VARCHAR(50),
                delivery_mode VARCHAR(50),
                observation TEXT,
                status INT,
                payment_status INT,
                customer_id BIGINT,
                product_id TEXT,
                shipping_tax NUMERIC(10, 2),
                shipping_tax_voucher_split TEXT,
                vouchers TEXT,
                proforms TEXT,
                attachments TEXT,
                cashed_co NUMERIC(10, 2),
                cashed_cod NUMERIC(10, 2),
                cancellation_request TEXT,
                has_editable_products DECIMAL,
                refunded_amount DECIMAL,
                is_complete INT,
                reason_cancellation TEXT,
                refund_status TEXT,
                maximum_date_for_shipment TIMESTAMP,
                late_shipment INT,
                flags TEXT,
                emag_club INT,
                finalization_date TIMESTAMP,
                details TEXT,
                weekend_delivery INT,
                payment_mode_id INT
            )
        """).format(sql.Identifier(orders_table))
        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(">>> Created order table <<<")
    except Exception as e:
        print(f"Failed to create table: {e}")

def count_all_orders(MARKETPLACE_API_URL, ORDERS_ENDPOINT, COUNT_ENGPOINT, API_KEY, PUBLIC_KEY=None, usePublicKey=False):
    url = f"{MARKETPLACE_API_URL}{ORDERS_ENDPOINT}/{COUNT_ENGPOINT}"
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

    data = json.dumps({
        "status": [1, 2, 3, 5]
    })
    response = requests.post(url, data=data, headers=headers, proxies=PROXIES)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve orders: {response.status_code}")
        return None
    
def get_all_orders(MARKETPLACE_API_URL, ORDERS_ENDPOINT, READ_ENDPOINT,  API_KEY, currentPage, PUBLIC_KEY=None, usePublicKey=False):
    url = f"{MARKETPLACE_API_URL}{ORDERS_ENDPOINT}/{READ_ENDPOINT}"
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
        "status": [1, 2, 3, 5]
    })
    response = requests.post(url, data=data, headers=headers, proxies=PROXIES)
    if response.status_code == 200:
        orders = response.json()
        return orders
    else:
        print(f"Failed to retrieve orders: {response.status_code}")
        return None

def safe_parse_datetime(date_str):
    if date_str is None:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        logging.error(f"Error parsing date: {date_str}")
        return None

def convert_to_json_string(data):
    if data is None:
        return None
    if isinstance(data, list):
        return json.dumps(data)
    return data

def parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

async def insert_orders(orders: List[Dict[str, Any]], db: AsyncSession):
    try:
        for order_data in orders:
            order = Order(
                vendor_name=order_data.get('vendor_name'),
                type=order_data.get('type'),
                parent_id=order_data.get('parent_id'),
                date=safe_parse_datetime(order_data.get('date')),
                payment_mode=order_data.get('payment_mode'),
                detailed_payment_method=order_data.get('detailed_payment_method'),
                delivery_mode=order_data.get('delivery_mode'),
                observation=order_data.get('observation'),
                status=order_data.get('status'),
                payment_status=order_data.get('payment_status'),
                customer_id=order_data.get('customer_id'),
                product_id=order_data.get('product_id'),
                shipping_tax=parse_float(order_data.get('shipping_tax')),
                shipping_tax_voucher_split=convert_to_json_string(order_data.get('shipping_tax_voucher_split')),
                vouchers=convert_to_json_string(order_data.get('vouchers')),
                proforms=convert_to_json_string(order_data.get('proforms')),
                attachments=convert_to_json_string(order_data.get('attachments')),
                cashed_co=parse_float(order_data.get('cashed_co')),
                cashed_cod=parse_float(order_data.get('cashed_cod')),
                has_editable_products=order_data.get('has_editable_products'),
                refunded_amount=parse_int(order_data.get('refunded_amount')),
                is_complete=order_data.get('is_complete'),
                refunded_reason_id=order_data.get('refunded_reason_id'),
                refund_status=order_data.get('refund_status'),
                maximum_date_for_shipment=safe_parse_datetime(order_data.get('maximum_date_for_shipment')),
                late_shipment=order_data.get('late_shipment'),
                flags=convert_to_json_string(order_data.get('flags')),
                emag_club=order_data.get('emag_club'),
                finalization_date=safe_parse_datetime(order_data.get('finalization_date')),
                details=convert_to_json_string(order_data.get('details')),
                weekend_delivery=order_data.get('weekend_delivery'),
                payment_mode_id=order_data.get('payment_mode_id'),
                sales=parse_float(order_data.get('sales')),
                unit=None,  # Set to None if data is not available
                gross_profit=None,  # Set to None if data is not available
                net_profit=None  # Set to None if data is not available
            )
            db.add(order)
        
        await db.commit()
        logging.info("###########Orders inserted successfully")
    except IntegrityError as e:
        logging.error(f"$$$$$$$$$$$$$Database integrity error: {e}")
        await db.rollback()
    except Exception as e:
        logging.error(f"%%%%%%%%%%%%%%%Failed to insert orders into database: {e}")
        await db.rollback()

async def insert_orders_into_db(orders, customers_table, orders_table):
    try:
        conn = psycopg2.connect(
            dbname=settings.DB_NAME,
            user=settings.DB_USERNAME,
            password=settings.DB_PASSOWRD,
            host=settings.DB_URL,
            port=settings.DB_PORT
        )
        conn.set_client_encoding('UTF8')
        cursor_order = conn.cursor()
        cursor_customer = conn.cursor()
        insert_customers_query = sql.SQL("""
            INSERT INTO {} (
                id,
                mkt_id,
                name,
                company,
                gender,
                phone_1,
                phone_2,
                phone_3,
                registration_number,
                code,
                email,
                billing_name,
                billing_phone,
                billing_country,
                billing_suburb,
                billing_city,
                billing_locality_id,
                billing_street,
                billing_postal_code,
                shipping_country,
                shipping_suburb,
                shipping_city,
                shipping_locality_id,
                shipping_postal_code,
                shipping_contact,
                shipping_phone,
                created,
                modified,
                bank,
                iban,
                legal_entity,
                fax,
                is_vat_payer,
                liable_person,
                shipping_street
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (id) DO UPDATE SET
                mkt_id = EXCLUDED.mkt_id,
                name = EXCLUDED.name,
                company = EXCLUDED.company,
                gender = EXCLUDED.gender,
                phone_1 = EXCLUDED.phone_1,
                phone_2 = EXCLUDED.phone_2,
                phone_3 = EXCLUDED.phone_3,
                registration_number = EXCLUDED.registration_number,
                code = EXCLUDED.code,
                email = EXCLUDED.email,
                billing_name = EXCLUDED.billing_name,
                billing_phone = EXCLUDED.billing_phone,
                billing_country = EXCLUDED.billing_country,
                billing_suburb = EXCLUDED.billing_suburb,
                billing_city = EXCLUDED.billing_city,
                billing_locality_id = EXCLUDED.billing_locality_id,
                billing_street = EXCLUDED.billing_street,
                billing_postal_code = EXCLUDED.billing_postal_code,
                shipping_country = EXCLUDED.shipping_country,
                shipping_suburb = EXCLUDED.shipping_suburb,
                shipping_city = EXCLUDED.shipping_city,
                shipping_locality_id = EXCLUDED.shipping_locality_id,
                shipping_postal_code = EXCLUDED.shipping_postal_code,
                shipping_contact = EXCLUDED.shipping_contact,
                shipping_phone = EXCLUDED.shipping_phone,
                created = EXCLUDED.created,
                modified = EXCLUDED.modified,
                bank = EXCLUDED.bank,
                iban = EXCLUDED.iban,
                legal_entity = EXCLUDED.legal_entity,
                fax = EXCLUDED.fax,
                is_vat_payer = EXCLUDED.is_vat_payer,
                liable_person = EXCLUDED.liable_person,
                shipping_street = EXCLUDED.shipping_street
            """).format(sql.Identifier(customers_table))
        insert_orders_query = sql.SQL("""
            INSERT INTO {} (
                id,
                vendor_name,
                type,
                parent_id,
                date,
                payment_mode,
                detailed_payment_method,
                delivery_mode,
                observation,
                status,
                payment_status,
                customer_id,
                product_id,
                shipping_tax,
                shipping_tax_voucher_split,
                vouchers,
                proforms,
                attachments,
                cashed_co,
                cashed_cod,
                cancellation_request,
                has_editable_products,
                refunded_amount,
                is_complete,
                reason_cancellation,
                refund_status,
                maximum_date_for_shipment,
                late_shipment,
                flags,
                emag_club,
                finalization_date,
                details,
                weekend_delivery,
                payment_mode_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (id) DO UPDATE SET
                vendor_name = EXCLUDED.vendor_name,
                type = EXCLUDED.type,
                parent_id = EXCLUDED.parent_id,
                date = EXCLUDED.date,
                payment_mode = EXCLUDED.payment_mode,
                detailed_payment_method = EXCLUDED.detailed_payment_method,
                delivery_mode = EXCLUDED.delivery_mode,
                observation = EXCLUDED.observation,
                status = EXCLUDED.status,
                payment_status = EXCLUDED.payment_status,
                customer_id = EXCLUDED.customer_id,
                product_id = EXCLUDED.product_id,
                shipping_tax = EXCLUDED.shipping_tax,
                shipping_tax_voucher_split = EXCLUDED.shipping_tax_voucher_split,
                vouchers = EXCLUDED.vouchers,
                proforms = EXCLUDED.proforms,
                attachments = EXCLUDED.attachments,
                cashed_co = EXCLUDED.cashed_co,
                cashed_cod = EXCLUDED.cashed_cod,
                cancellation_request = EXCLUDED.cancellation_request,
                has_editable_products = EXCLUDED.has_editable_products,
                refunded_amount = EXCLUDED.refunded_amount,
                is_complete = EXCLUDED.is_complete,
                reason_cancellation = EXCLUDED.reason_cancellation,
                refund_status = EXCLUDED.refund_status,
                maximum_date_for_shipment = EXCLUDED.maximum_date_for_shipment,
                late_shipment = EXCLUDED.late_shipment,
                flags = EXCLUDED.flags,
                emag_club = EXCLUDED.emag_club,
                finalization_date = EXCLUDED.finalization_date,
                details = EXCLUDED.details,
                weekend_delivery = EXCLUDED.weekend_delivery,
                payment_mode_id = EXCLUDED.payment_mode_id
            """).format(sql.Identifier(orders_table))
        
        for order in orders:
            customer = order.get('customer', {})
            customer_id = customer.get('id')
            if customer_id is None:
                logging.error(f"Missing customer ID for order: {order.get('id')}")
                continue
            customer_mkt_id = customer.get('mkt_id')
            customer_name = customer.get('name')
            customer_company = customer.get('company')
            customer_gender = customer.get('gender')
            customer_phone_1 = customer.get('phone_1')
            customer_phone_2 = customer.get('phone_2')
            customer_phone_3 = customer.get('phone_3')
            customer_registration_number = customer.get('registration_number')
            customer_code = customer.get('code')
            customer_email = customer.get('email')
            customer_billing_name = customer.get('billing_name')
            customer_billing_phone = customer.get('billing_phone')
            customer_billing_country = customer.get('billing_country')
            customer_billing_suburb = customer.get('billing_suburb')
            customer_billing_city = customer.get('billing_city')
            customer_billing_locality_id = customer.get('billing_locality_id')
            customer_billing_street = customer.get('billing_street')
            customer_billing_postal_code = customer.get('billing_postal_code')
            customer_shipping_country = customer.get('shipping_country')
            customer_shipping_suburb = customer.get('shipping_suburb')
            customer_shipping_city = customer.get('shipping_city')
            customer_shipping_locality_id = customer.get('shipping_locality_id')
            customer_shipping_postal_code = customer.get('shipping_postal_code')
            customer_shipping_contact = customer.get('shipping_contact')
            customer_shipping_phone = customer.get('shipping_phone')
            customer_created = customer.get('created')
            customer_modified = customer.get('modified')
            customer_bank = customer.get('bank')
            customer_iban = customer.get('iban')
            customer_legal_entity = customer.get('legal_entity')
            customer_fax = customer.get('fax')
            customer_is_vat_payer = customer.get('is_vat_payer')
            customer_liable_person = customer.get('liable_person')
            customer_shipping_street = customer.get('shipping_street')

            cursor_customer.execute(insert_customers_query, (
                customer_id,
                customer_mkt_id,
                customer_name,
                customer_company,
                customer_gender,
                customer_phone_1,
                customer_phone_2,
                customer_phone_3,
                customer_registration_number,
                customer_code,
                customer_email,
                customer_billing_name,
                customer_billing_phone,
                customer_billing_country,
                customer_billing_suburb,
                customer_billing_city,
                customer_billing_locality_id,
                customer_billing_street,
                customer_billing_postal_code,
                customer_shipping_country,
                customer_shipping_suburb,
                customer_shipping_city,
                customer_shipping_locality_id,
                customer_shipping_postal_code,
                customer_shipping_contact,
                customer_shipping_phone,
                customer_created,
                customer_modified,
                customer_bank,
                customer_iban,
                customer_legal_entity,
                customer_fax,
                customer_is_vat_payer,
                customer_liable_person,
                customer_shipping_street
            ))

            id = order.get('id')
            vendor_name = order.get('vendor_name')
            type = order.get('type')
            parent_id = order.get('parent_id')
            date = order.get('date')
            payment_mode = order.get('payment_mode')
            detailed_payment_method = order.get('detailed_payment_method')
            delivery_mode = order.get('delivery_mode')
            observation = order.get('observation')
            status = order.get('status')
            payment_status = order.get('payment_status')
            customer_id = customer_id
            products_id = json.dumps([product.get('product_id') for product in order.get('products', [])])
            shipping_tax = order.get('shipping_tax')
            shipping_tax_voucher_split = json.dumps(order.get('shipping_tax_voucher_split', []))
            vouchers = json.dumps(order.get('vouchers', []))
            proforms = json.dumps(order.get('proforms', []))
            attachments = json.dumps(order.get('attachments', []))
            cashed_co = order.get('cashed_co')
            cashed_cod = order.get('cashed_cod')
            cancellation_request = order.get('cancellation_request')
            has_editable_products = order.get('has_editable_products')
            refunded_amount = order.get('refunded_amount')
            is_complete = order.get('is_complete')
            reason_cancellation = json.dumps(order.get('reason_cancellation', {}))
            refund_status = order.get('refund_status')
            maximum_date_for_shipment = order.get('maximum_date_for_shipment')
            late_shipment = order.get('late_shipment')
            flags = json.dumps(order.get('flags', []))
            emag_club = order.get('emag_club')
            finalization_date = order.get('finalization_date')
            details = json.dumps(order.get('details', {}))
            weekend_delivery = order.get('weekend_delivery')
            payment_mode_id = order.get('payment_mode_id')
            
            cursor_order.execute(insert_orders_query, (
                id,
                vendor_name,
                type,
                parent_id,
                date,
                payment_mode,
                detailed_payment_method,
                delivery_mode,
                observation,
                status,
                payment_status,
                customer_id,
                products_id,
                shipping_tax,
                shipping_tax_voucher_split,
                vouchers,
                proforms,
                attachments,
                cashed_co,
                cashed_cod,
                cancellation_request,
                has_editable_products,
                refunded_amount,
                is_complete,
                reason_cancellation,
                refund_status,
                maximum_date_for_shipment,
                late_shipment,
                flags,
                emag_club,
                finalization_date,
                details,
                weekend_delivery,
                payment_mode_id
            ))
        
        conn.commit()
        cursor_order.close()
        cursor_customer.close()
        conn.close()
        print("Orders inserted successfully")
    except Exception as e:
        print(f"Failed to insert orders into database: {e}")

async def refresh_orders(marketplace: Marketplace, db:AsyncSession):
    # create_database()

    logging.info(f">>>>>>> Refreshing Marketplace : {marketplace.title} <<<<<<<<")
    customer_table = f"{marketplace.marketplaceDomain.replace('.', '_')}_customers"
    orders_table = f"{marketplace.marketplaceDomain.replace('.', '_')}_orders"
    create_customers_table(customer_table)
    create_orders_table(orders_table)

    if marketplace.credentials["type"] == "user_pass":
        USERNAME = marketplace.credentials["firstKey"]
        PASSWORD = marketplace.credentials["secondKey"]
        API_KEY = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode('utf-8'))
        result = count_all_orders(marketplace.baseAPIURL, marketplace.orders_crud["endpoint"], marketplace.orders_crud["count"], API_KEY)
        if result:
            pages = result['results']['noOfPages']
            items = result['results']['noOfItems']

            logging.info(f"Number of Pages: {pages}")
            logging.info(f"Number of Items: {items}")

            # currentPage = int(pages)
            currentPage = 1
            baseAPIURL = marketplace.baseAPIURL
            endpoint = marketplace.orders_crud['endpoint']
            read_endpoint = marketplace.orders_crud['read']
            try:
                while currentPage <= 2:
                    orders = get_all_orders(baseAPIURL, endpoint, read_endpoint, API_KEY, currentPage)
                    print(f">>>>>>> Current Page : {currentPage} <<<<<<<<")
                    if orders and orders['isError'] == False:
                        async with db as session:
                            await insert_orders_into_db(orders['results'], customer_table, orders_table)
                            # await insert_orders(orders['results'], session)
                        currentPage += 1
            except Exception as e:
                print('++++++++++++++++++++++++++++++++++++++++++')
                print(e)

    