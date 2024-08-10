import asyncio
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from sqlalchemy import select
from app.routers import auth, internal_products, returns, users, shipment, profile, marketplace, utils, orders, dashboard, supplier, inventory, AWB_generation, notifications, customer, warehouse
from app.database import Base, engine
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.emag_products import refresh_emag_products
from app.utils.emag_orders import refresh_emag_orders, refresh_emag_all_orders
from app.utils.emag_returns import refresh_emag_returns
from app.utils.emag_reviews import refresh_emag_reviews
from app.utils.emag_awbs import *
from app.utils.emag_locality import refresh_emag_localities
from app.utils.emag_courier import refresh_emag_couriers
from app.utils.altex_product import refresh_altex_products
from app.utils.altex_orders import refresh_altex_orders
from app.utils.altex_courier import refresh_altex_couriers
from app.utils.altex_returns import refresh_altex_rmas
from app.utils.altex_location import refresh_altex_locations
from app.routers.reviews import *
from app.models.marketplace import Marketplace
from sqlalchemy.orm import Session
import ssl
import logging



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
#             result = await session.execute(select(Marketplace))
#             marketplaces = result.scalars().all()
#             logging.info(f"Success getting {len(marketplaces)} marketplaces")
#             for marketplace in marketplaces:
#                 if marketplace.marketplaceDomain == "altex.ro":
#                     logging.info("Refresh locations from altex")
#                     await refresh_altex_locations(marketplace)
#                     logging.info("Refresh couriers from altex")
#                     await refresh_altex_couriers(marketplace)
#                 else:
#                     logging.info("Refresh localities from marketplace")
#                     await refresh_emag_localities(marketplace)
#                     logging.info("Refresh couriers refresh")
#                     await refresh_emag_couriers(marketplace)
#                     logging.info("Refresh orders form marketplace")
#                     await refresh_emag_all_orders(marketplace, session)
#                     continue

@app.on_event("startup")
@repeat_every(seconds=86400)  # Run daily for deleting video last 30 days
async def refresh_data(db: AsyncSession = Depends(get_db)): 
    async for db in get_db():
        async with db as session:
            logging.info("Starting product refresh")
            result = await session.execute(select(Marketplace))
            marketplaces = result.scalars().all()
            logging.info(f"Success getting {len(marketplaces)} marketplaces")
            for marketplace in marketplaces:
                if marketplace.marketplaceDomain == "altex.ro":
                    logging.info("Refresh rmas from altex")
                    await refresh_altex_rmas(marketplace)
                else:
                    logging.info("Refresh refunds from marketplace")
                    await refresh_emag_returns(marketplace)
                    logging.info("Check hijacker and review")
                    await check_hijacker_and_bad_reviews(marketplace, session)
                    # logging.info("Refresh awb from marketplace")
                    # await refresh_emag_awb(marketplace, session)


@app.on_event("startup")
@repeat_every(seconds=600)
async def refresh_orders_data(db:AsyncSession = Depends(get_db)):
    async for db in get_db():
        async with db as session:
            logging.info("Starting orders refresh")
            result = await session.execute(select(Marketplace))
            marketplaces = result.scalars().all()
            for marketplace in marketplaces:
                if marketplace.marketplaceDomain == "altex.ro":
                    logging.info("Refresh products from marketplace")
                    await refresh_altex_products(marketplace)
                    
                    logging.info("Refresh orders from marketplace")
                    await refresh_altex_orders(marketplace)
                else:
                    logging.info("Refresh products from marketplace")
                    await refresh_emag_products(marketplace, session)
                    logging.info("Refresh orders from marketplace")
                    await refresh_emag_orders(marketplace, session)
                    continue


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("refresh_data:app", host="0.0.0.0", port=3000, reload=False)
    