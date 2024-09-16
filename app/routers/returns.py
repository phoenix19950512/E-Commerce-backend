from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, any_, or_, cast, Integer
from typing import List
from app.database import get_db
from app.models.product import Product
from app.models.returns import Returns
from app.schemas.returns import ReturnsCreate, ReturnsRead, ReturnsUpdate

router = APIRouter()

@router.post("/", response_model=ReturnsRead)
async def create_return(returns: ReturnsCreate, db: AsyncSession = Depends(get_db)):
    db_return = Returns(**returns.dict())
    db.add(db_return)
    await db.commit()
    await db.refresh(db_return)
    return db_return

@router.get('/count')
async def get_return_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(func.count(Returns.order_id))
    count = result.scalar()
    return count

@router.get("/")
async def get_returns(
    page: int = Query(1, ge=1, description="page number"),
    items_per_page: int = Query(50, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * items_per_page
    result = await db.execute(select(Returns).offset(offset).limit(items_per_page))
    db_returns = result.scalars().all()
    if db_returns is None:
        raise HTTPException(status_code=404, detail="return not found")
    
    return_data = []
    for db_return in db_returns:
        product_ids = db_return.products
        marketplace = db_return.return_market_place
        ean = []

        for product_id in product_ids:
            result = await db.execute(select(Product).where(Product.id == product_id, Product.product_marketplace == marketplace))
            product = result.scalars().first()
            if product is None:
                result = await db.execute(select(Product).where(Product.id == product_id))
                product = result.scalars().first()
            ean.append(product.ean) 
        
        return_data.append({
            **{column.name: getattr(db_return, column.name) for column in Returns.__table__.columns},
            "ean": ean
        })
    return return_data

@router.get("/return_id")
async def get_return_info(return_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Returns).where(cast(Returns.emag_id, Integer) == return_id))
    db_return = result.scalars().first
    if db_return is None:
        raise HTTPException(status_code=404, detail="awb not found")
    return db_return

@router.get("/awb")
async def get_return_awb(awb: str, db: AsyncSession = Depends(get_db)):
    if awb[:2] == "01":
        result = await db.execute(select(Returns).where(or_(Returns.awb == awb[2:], Returns.awb == awb[2:-3], Returns.awb == awb, Returns.awb == awb[:-3])))
    else:
        result = await db.execute(select(Returns).where(or_(Returns.awb == awb, Returns.awb == awb[:-3])))
    db_return = result.scalars().first()
    if db_return is None:
        raise HTTPException(status_code=404, detail="awb not found")
    
    product_ids = db_return.products
    marketplace = db_return.return_market_place
    ean = []

    for product_id in product_ids:
        result = await db.execute(select(Product).where(Product.id == product_id, Product.product_marketplace == marketplace))
        product = result.scalars().first()
        if product is None:
            result = await db.execute(select(Product).where(Product.id == product_id))
            product = result.scalars().first()
        ean.append(product.ean)

    return {
        **{column.name: getattr(db_return, column.name) for column in Returns.__table__.columns},
        "ean": ean
    }

@router.put("/{return_id}", response_model=ReturnsRead)
async def update_return(return_id: int, returns: ReturnsUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Returns).filter(Returns.order_id == return_id))
    db_return = result.scalars().first()
    if db_return is None:
        raise HTTPException(status_code=404, detail="return not found")
    for var, value in vars(returns).items():
        setattr(db_return, var, value) if value is not None else None
    await db.commit()
    await db.refresh(db_return)
    return db_return

@router.delete("/{return_id}", response_model=ReturnsRead)
async def delete_return(return_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Returns).filter(Returns.order_id == return_id))
    returns = result.scalars().first()
    if ReturnsCreate is None:
        raise HTTPException(status_code=404, detail="return not found")
    await db.delete(returns)
    await db.commit()
    return Returns
