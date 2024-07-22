import asyncio
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from sqlalchemy import select
from app.routers import auth, returns, users, products, shipment, profile, marketplace, utils, orders, dashboard, supplier, inventory, AWB_generation, notifications, customer
from app.database import Base, engine
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.emag_products import *
from app.utils.emag_orders import *
from app.utils.emag_returns import *
from app.utils.emag_reviews import *
from app.utils.emag_awbs import *
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
async def on_startup():
    await init_models()

@app.on_event("startup")
@repeat_every(seconds=86400)  # Run daily for deleting video last 30 days
async def refresh_data(db: AsyncSession = Depends(get_db)):
    settings.products_table_name = []
    settings.orders_table_name = []
    settings.notifications_table_name = []
    settings.customers_table_name = []
    settings.returns_table_name = []
    settings.reviews_table_name = []

    async for db in get_db():
        async with db as session:
            logging.info("Starting product refresh")
            result = await session.execute(select(Marketplace))
            marketplaces = result.scalars().all()
            logging.info(f"Success getting {len(marketplaces)} marketplaces")
            for marketplace in marketplaces:
                logging.info("Refresh product from marketplace")
                # await refresh_products(marketplace, session)
                logging.info("Refresh refunds from marketplace")
                # await refresh_returns(marketplace)
                logging.info("Refresh order from marketplace")
                # await refresh_orders(marketplace, session)
                logging.info("Check hijacker and review")
                # await check_hijacker_and_bad_reviews(marketplace, session)
                logging.info("Refresh awb from marketplace")
                await refresh_awb(marketplace, session)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(profile.router, prefix="/profile", tags=["profile"])
app.include_router(marketplace.router, prefix="/api/marketplace", tags=["marketplace"])
app.include_router(utils.router, prefix="/api/utils", tags=["utils"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(supplier.router, prefix="/api/suppliers", tags=["supppliers"])
app.include_router(shipment.router, prefix="/api/shipment", tags=["shipment"])
app.include_router(returns.router, prefix="/api/returns", tags=["returns"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["inventory"])
app.include_router(AWB_generation.router, prefix="/awb", tags=["awb"])
app.include_router(notifications.router, prefix='/api/notifications', tags=["notifications"])
app.include_router(customer.router, prefix='/api/customers', tags=["customers"])

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
if __name__ == "__main__":
    # Check if SSL arguments are provided
    import uvicorn
    ssl_keyfile = "ssl/key.pem"
    ssl_certfile = "ssl/cert.pem"
    # if ssl_keyfile and ssl_certfile:
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        # reload=True  # Optional: Enables auto-reload for code changes
    )
    # else:
    #     print("SSL keyfile or certfile not found. Running without SSL.")
    #     uvicorn.run(
    #         "main:app",
    #         host="0.0.0.0",
    #         port=8000,
    #         reload=True  # Optional: Enables auto-reload for code changes
    #     )