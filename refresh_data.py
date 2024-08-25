import asyncio
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from sqlalchemy import select
from sqlalchemy import any_
from app.routers import auth, internal_products, returns, users, shipment, profile, marketplace, utils, orders, dashboard, supplier, inventory, AWB_generation, notifications, customer, warehouse
from app.database import Base, engine
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.emag_products import refresh_emag_products, post_stock_emag
from app.utils.emag_orders import refresh_emag_orders, refresh_emag_all_orders
from app.utils.emag_returns import refresh_emag_returns
from app.utils.emag_reviews import refresh_emag_reviews
from app.utils.emag_awbs import *
from app.utils.emag_locality import refresh_emag_localities
from app.utils.emag_courier import refresh_emag_couriers
from app.utils.altex_product import refresh_altex_products, post_stock_altex
from app.utils.altex_orders import refresh_altex_orders
from app.utils.altex_courier import refresh_altex_couriers
from app.utils.altex_returns import refresh_altex_rmas
from app.utils.altex_location import refresh_altex_locations
from app.utils.smart_api import get_stock
from app.routers.reviews import *
from app.models.marketplace import Marketplace
from app.models.billing_software import Billing_software
from app.models.orders import Order
from sqlalchemy.orm import Session
import ssl
import logging
from sqlalchemy import update



# member
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
# from module import Member, get_member, check_access

app = FastAPI()

class MemberResponse(BaseModel):
    username: str
    role_name: str
    access_level: str


app = FastAPI()

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain('ssl/cert.pem', keyfile='ssl/key.pem')

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# @app.on_event("startup")
# async def on_startup(db: AsyncSession = Depends(get_db)):
#     await init_models()
    
#     async for db in get_db():
#         async with db as session:
#             logging.info("Starting localities refresh")
#             result = await session.execute(select(Marketplace).order_by(Marketplace.id.asc()))
#             marketplaces = result.scalars().all()
#             logging.info(f"Success getting {len(marketplaces)} marketplaces")
#             for marketplace in marketplaces:
#                 if marketplace.marketplaceDomain == "altex.ro":
#                     # logging.info("Refresh locations from altex")
#                     # await refresh_altex_locations(marketplace)
#                     # logging.info("Refresh couriers from altex")
#                     # await refresh_altex_couriers(marketplace)
#                     continue
#                 else:
#                     # logging.info("Refresh localities from marketplace")
#                     # await refresh_emag_localities(marketplace)
#                     # logging.info("Refresh couriers refresh")
#                     # await refresh_emag_couriers(marketplace)
#                     # logging.info("Refresh orders form marketplace")
#                     # await refresh_emag_all_orders(marketplace, session)
#                     continue

# @app.on_event("startup")
# @repeat_every(seconds=900)
# async def refresh_orders_data(db:AsyncSession = Depends(get_db)):
#     async for db in get_db():
#         async with db as session:
#             logging.info("Starting orders refresh")
#             result = await session.execute(select(Marketplace).order_by(Marketplace.id.asc()))
#             marketplaces = result.scalars().all()
#             logging.info(f"Success getting {len(marketplaces)} marketplaces")
#             for marketplace in marketplaces:
#                 if marketplace.marketplaceDomain == "altex.ro":
#                     logging.info("Refresh products from marketplace")
#                     await refresh_altex_products(marketplace)
#                     logging.info("Refresh orders from marketplace")
#                     await refresh_altex_orders(marketplace)
#                 else:
#                     logging.info("Refresh products from marketplace")
#                     await refresh_emag_products(marketplace)
#                     logging.info("Refresh orders from marketplace")
#                     await refresh_emag_orders(marketplace)

@app.on_event("startup")
@repeat_every(seconds=900)
async def send_stock(db:AsyncSession = Depends(get_db)):
    async for db in get_db():
        async with db as session:
            logging.info("Init orders_stock")
            await session.execute(update(Internal_Product).values(orders_stock=0))
            await session.commit()
            logging.info("Calculate orders_stock")
            result = await session.execute(select(Order).where(Order.status == any_([1,2,3])))
            db_new_orders = result.scalars().all()
            if db_new_orders is None:
                logging.info("Can't find new orders")
                return
            for db_new_order in db_new_orders:
                product_id_list = db_new_order.product_id
                quantity_list = db_new_order.quantity
                marketplace = db_new_order.order_market_place
                for i in range(len(product_id_list)):
                    product_id = product_id_list[i]
                    quantity = quantity_list[i]
                
                    result = await session.execute(select(Product).where(Product.id == product_id, Product.product_marketplace == marketplace))
                    db_product = result.scalars().first()
                    if db_product is None:
                        logging.info(f"Can't find {product_id} in {marketplace}")
                    ean = db_product.ean

                    result = await session.execute(select(Internal_Product).where(Internal_Product.ean == ean))
                    db_internal_product = result.scalars().first()
                    if db_internal_product is None:
                        logging.info(f"Can't find {ean}")
                    db_internal_product.orders_stock = db_internal_product.orders_stock + quantity

                    await db.commit()
                    await db.refresh(db_product)
            logging.info("Sync stock")
            result = await session.execute(select(Internal_Product))
            db_products = result.scalars().all()
            for product in db_products:
                ean = product.ean
                marketplaces = product.market_place
                for domain in marketplaces:
                    result = await session.execute(select(Marketplace).where(Marketplace.marketplaceDomain == domain))
                    marketplace = result.scalars().first()

                    result = await session.execute(select(Product).where(Product.ean == ean, Product.product_marketplace == domain))
                    db_product = result.scalars().first()
                    product_id = db_product.id
                    stock = product.smartbill_stock - product.orders_stock - product.damaged_goods
                    
                    if marketplace.marketplaceDomain == "altex.ro":
                        if db_product.barcode_title == "":
                            continue
                        post_stock_altex(marketplace, db_product.barcode_title, stock)
                        logging.info("post stock success in altex")
                    else:
                        post_stock_emag(marketplace, product_id, stock)      
                        logging.info("post stock success in emag")              

# @app.on_event("startup")
# @repeat_every(seconds=7200)
# async def refresh_stock(db: AsyncSession = Depends(get_db)):
#     async for db in get_db():
#         async with db as session:
#             logging.info("Starting stock refresh")
#             result = await session.execute(select(Billing_software))
#             db_smarts = result.scalars().all()
#             if db_smarts is None:
#                 logging.info("Can't find billing software")
#             else:
#                 logging.info("Fetch stock via smarbill api")
#                 product_code_list = []
#                 for db_smart in db_smarts:
#                     products_list = get_stock(db_smart)
#                     for products in products_list:
#                         products = products.get('products')
#                         for product in products:
#                             logging.info(product)
#                             product_code = product.get('productCode')
#                             logging.info(f"Update stock {product_code}")
#                             result = await session.execute(select(Internal_Product).where(Internal_Product.product_code == product_code))
#                             db_product = result.scalars().first()
#                             if db_product is None:
#                                 product_code_list.append({
#                                     "product_code": product_code,
#                                     "quantity": int(product.get('quantity'))
#                                 })
#                                 continue
#                             db_product.smartbill_stock = int(product.get('quantity'))
#                             await db.commit()
#                             await db.refresh(db_product)
#                 logging.info(f"product_code_list: {product_code_list}")
#                 logging.info("Finish sync stock")

# @app.on_event("startup")
# @repeat_every(seconds=86400)  # Run daily for deleting video last 30 days
# async def refresh_data(db: AsyncSession = Depends(get_db)): 
#     async for db in get_db():
#         async with db as session:
#             logging.info("Starting product refresh")
#             result = await session.execute(select(Marketplace).order_by(Marketplace.id.asc()))
#             marketplaces = result.scalars().all()
#             logging.info(f"Success getting {len(marketplaces)} marketplaces")
#             for marketplace in marketplaces:
#                 if marketplace.marketplaceDomain == "altex.ro":
#                     logging.info("Refresh rmas from altex")
#                     await refresh_altex_rmas(marketplace)
#                     continue
#                 else:
#                     logging.info("Refresh refunds from marketplace")
#                     await refresh_emag_returns(marketplace)
#                     # logging.info("Refresh reviews from emag")
#                     # await refresh_emag_reviews(marketplace, session)
#                     logging.info("Check hijacker and review")
#                     await check_hijacker_and_bad_reviews(marketplace, session)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("refresh_data:app", host="0.0.0.0", port=3000, reload=False)
    