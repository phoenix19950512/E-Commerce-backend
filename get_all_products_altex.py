import requests
import psycopg2
import base64
import json
import hashlib
import time
import urllib.parse
from psycopg2 import sql
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

MARKETPLACE_URL = 'https://marketplace.altex.ro'
# MARKETPLACE_API_URL = 'https://marketplace.altex.ro/v2.0/catalog'
MARKETPLACE_API_URL = 'https://mkp-stage.altex.ro/v1.0/sales'
PRODUCTS_ENDPOINT = "/order"

PROXIES = {
    'http': 'http://p2p_user:jDkAx4EkAyKw@65.109.7.74:54021',
    'https': 'http://p2p_user:jDkAx4EkAyKw@65.109.7.74:54021',
}

DB_NAME = "e_commerce"
DB_USER = "dev"
DB_PASSWORD = "dev"
DB_HOST = "localhost"
DB_PORT = "5432"

def create_database():
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
        cursor.close()
        conn.close()
        print(">>> Created database <<<")
    except Exception as e:
        print(f"Failed to create database: {e}")

def create_products_table():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        create_table_query = """
            CREATE TABLE IF NOT EXISTS products_altex (
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
                ean TEXT,
                commission NUMERIC(16, 4),
                validation_status TEXT,
                translation_validation_status TEXT,
                offer_validation_status TEXT,
                auto_translated INTEGER,
                ownership BOOLEAN,
                best_offer_sale_price NUMERIC(16, 4),
                best_offer_recommended_price NUMERIC(16, 4),1.1
                number_of_offers INTEGER,
                genius_eligibility INTEGER,
                recycleWarranties INTEGER
            )
        """
        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
        conn.close()
        print(">>> Created table <<<")
    except Exception as e:
        print(f"Failed to create table: {e}")

def count_all_products(API_KEY):
    url = f"{MARKETPLACE_API_URL}{PRODUCTS_ENDPOINT}/count"
    api_key = str(API_KEY).replace("b'", '').replace("'", "")
    print(api_key)
    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve products: {response.status_code}")
        return None
    
def get_all_products(API_KEY, currentPage):
    url = f"{MARKETPLACE_API_URL}{PRODUCTS_ENDPOINT}/read"
    api_key = str(API_KEY).replace("b'", '').replace("'", "")
    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "itemsPerPage": 100,
        "currentPage": currentPage,
    })
    response = requests.post(url, data=data, headers=headers)
    if response.status_code == 200:
        products = response.json()
        return products
    else:
        print(f"Failed to retrieve products: {response.status_code}")
        return None

def insert_products_into_db(products, username):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        insert_query = sql.SQL("""
            INSERT INTO products_altex (
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
        """)

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
    
def http_build_query(params, separator='|'):
    return separator.join([urllib.parse.quote_plus(str(k)) + '=' + urllib.parse.quote_plus(str(v)) for k, v in params.items()])

def get_signature(public_key, private_key, page_nr=1, items_per_page=100):
    request_params = {
        'page_nr': f"{page_nr}",
        'items_per_page': f"{items_per_page}"
    }
    # url_query_string = urllib.parse.urlencode(
    #     request_params,
    #     safe='|',
    #     quote_via=urllib.parse.quote
    # )

    # Generate the URL query string
    url_query_string = urllib.parse.urlencode(request_params, doseq=True, safe='|')

    # current_timestamp = int(time.time())
    # remainder = current_timestamp % 10000
    # time_digits = str(remainder).zfill(4)
    time_digits = str(int(time.time()))[-4:]
    print(url_query_string)
    print(hashlib.sha512(private_key.encode()).hexdigest())
    # current_time = str(int(time.time()))
    # time_digits = current_time[-4:]
    string_to_hash = f"{public_key}||{hashlib.sha512(private_key.encode()).hexdigest()}||{url_query_string}||{time_digits}"
    hash_value = hashlib.sha512(string_to_hash.encode()).hexdigest().lower()
    print(hash_value)
    signature = time_digits + hash_value
    print(signature)
    return signature

def insert_get_product(url, public_key, private_key):
    METHOD = 'GET'
    headers = {
        "X-Request-Public-Key": f"{public_key}",
        "X-Request-Signature": f"{get_signature(public_key, private_key, page_nr=1, items_per_page=100)}"
    }

    try:
        response = requests.request(METHOD, url, headers=headers, verify=False, allow_redirects=True)
        if response.status_code == 200:
            print(response.json())
            return response.json()
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)
            return response.text

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    return 'error'

if __name__ == "__main__":
    # create_database()
    # create_products_table()
    PUBLIC_KEY = "d36e0f510bc852a4b00057f4be52442d"
    PRIVATE_KEY = "62d5328f778729a1561ae9ea3d8fc5e8"
    insert_get_product(f"{MARKETPLACE_API_URL}{PRODUCTS_ENDPOINT}", PUBLIC_KEY, PRIVATE_KEY)
    # API_KEY = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode('utf-8'))
    # result = count_all_products(API_KEY)['results']
    # pages = result['noOfPages']
    # items = result['noOfItems']
    # print(items)
    # currentPage = 1
    # while currentPage < int(pages) + 1:
    #     products = get_all_products(API_KEY, currentPage)
    #     print(f">>>>>>> Current Page : {currentPage} <<<<<<<<")
    #     print(len(products['results']))
    #     if products and products['isError'] == False:
    #         insert_products_into_db(products['results'], USERNAME)
    #         currentPage += 1