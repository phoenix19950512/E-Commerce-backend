import asyncio
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from sqlalchemy import select
from app.routers import auth, returns, users, products, shipment, profile, marketplace, utils, orders, dashboard, supplier, inventory, AWB_generation, notifications, customer, warehouse
from app.database import Base, engine
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.emag_products import *
from app.utils.emag_orders import *
from app.utils.emag_returns import *
from app.utils.emag_reviews import *
from app.utils.emag_awbs import *
from app.utils.emag_locality import *
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

@app.on_event("startup")
async def on_startup(db: AsyncSession = Depends(get_db)):
    await init_models()
    
    async for db in get_db():
        async with db as session:
            logging.info("Starting product refresh")
            result = await session.execute(select(Marketplace))
            marketplaces = result.scalars().all()
            logging.info(f"Success getting {len(marketplaces)} marketplaces")
            for marketplace in marketplaces:
                logging.info("Refresh product from marketplace")
                await refresh_localities(marketplace)

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
                logging.info("Refresh product from marketplace")
                await refresh_products(marketplace, session)
                logging.info("Refresh refunds from marketplace")
                await refresh_returns(marketplace)
                logging.info("Refresh order from marketplace")
                await refresh_orders(marketplace, session)
                logging.info("Check hijacker and review")
                await check_hijacker_and_bad_reviews(marketplace, session)
                logging.info("Refresh awb from marketplace")
                await refresh_awb(marketplace, session)


@app.on_event("startup")
@repeat_every(seconds=600)
async def refresh_orders_data(db:AsyncSession = Depends(get_db)):
    async for db in get_db():
        async with db as session:
            logging.info("Starting orders refresh")
            result = await session.execute(select(Marketplace))
            marketplaces = result.scalars().all()
            for marketplace in marketplaces:
                logging.info("Refresh orders from marketplace")
                await refresh_orders(marketplace, session)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("refresh_data:app", host="0.0.0.0", port=3000, reload=True)
    