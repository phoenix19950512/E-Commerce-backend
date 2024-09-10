from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import aliased
from sqlalchemy import func, any_, or_, and_
from typing import List
from sqlalchemy import cast, String
from app.database import get_db
from app.models.awb import AWB
from app.models.orders import Order
from app.models.product import Product
from app.models.invoice import Invoice
from app.models.replacement import Replacement
from app.schemas.replacement import ReplacementsCreate, ReplacementsRead, ReplacementsUpdate

router = APIRouter()

@router.post("/", response_model=ReplacementsRead)
async def create_replacement(replacement: ReplacementsCreate, db: AsyncSession = Depends(get_db)):
    db_replacement = Replacement(**replacement.dict())
    order_id = db_replacement.order_id
    result = await db.execute(select(Replacement).where(Replacement.order_id == order_id))
    replacements = result.scalars().all()
    count = len(replacements)
    db_replacement.number = count + 1
    db.add(db_replacement)
    await db.commit()
    await db.refresh(db_replacement)
    return db_replacement

@router.get('/count')
async def get_replacement_count(
    search_text: str = Query('', description="Text for searching"),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Replacement).filter(
        (cast(Replacement.order_id, String).ilike(f"%{search_text}%")) |
        (Replacement.awb.ilike(f"%{search_text}%")) |
        (Replacement.customer_name.ilike(f"%{search_text}%"))
    ))
    db_replacements = result.scalars().all()
    return len(db_replacements)

@router.get('/count_without_awb')
async def get_count_without_awb(db:AsyncSession = Depends(get_db)):
    AWBAlias = aliased(AWB)
    query = select(Replacement, AWBAlias).outerjoin(
        AWBAlias,
        and_(
            Replacement.order_id == AWBAlias.order_id,
            Replacement.number == -AWBAlias.number
        )
    )
    result = await db.execute(query)
    db_replacements = result.all()
    cnt = 0

    for replacement, awb in db_replacements:
        if awb is None:
            cnt += 1
    return cnt

@router.get("/")
async def get_replacements(
    page: int = Query(1, ge=1, description="Page number"),
    itmes_per_page: int = Query(50, ge=1, le=100, description="Number of items per page"),
    status: int = Query(0, description="status"),
    search_text: str = Query('', description="Text for searching"),
    db: AsyncSession = Depends(get_db)
):
    AWBAlias = aliased(AWB)
    InvoiceAlias = aliased(Invoice)
    OrderAlias = aliased(Order)
    query = select(Replacement, AWBAlias, InvoiceAlias, OrderAlias).outerjoin(
        AWBAlias,
        and_(
            Replacement.order_id == AWBAlias.order_id,
            Replacement.number == -AWBAlias.number
        )
    ).outerjoin(
        InvoiceAlias,
        InvoiceAlias.replacement_id == Replacement.id
    ).outerjoin(
        OrderAlias,
        OrderAlias.id == Replacement.order_id
    ).filter(
        (cast(Replacement.order_id, String).ilike(f"%{search_text}%")) |
        (Replacement.awb.ilike(f"%{search_text}%")) |
        (Replacement.customer_name.ilike(f"%{search_text}%"))
    )
    if status == 1:
        query = query.where(AWBAlias.order_id.is_(None))
    offset = (page - 1) * itmes_per_page
    result = await db.execute(query.offset(offset).limit(itmes_per_page))
    db_replacements = result.all()

    if db_replacements is None:
        raise HTTPException(status_code=404, detail="replacement not found")
    
    replacement_data = []
    for replacement, awb, invoice, order in db_replacements:
        ean = []
        if order is not None:
            product_ids = order.product_id
            for product_id in product_ids:
                result = await db.execute(select(Product).where(Product.id == product_id, Product.product_marketplace == order.order_market_place))
                product = result.scalars().first()
                ean.append(product.ean)
        replacement_data.append({
            **{column.name: getattr(replacement, column.name) for column in replacement.__table__.columns},
            "awb": awb,
            "invoice": invoice,
            "order": order,
            "ean": ean
        })
    
    return replacement_data

@router.get("/{replacement_id}", response_model=ReplacementsRead)
async def get_replacement(replacement_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Replacement).filter(Replacement.id == replacement_id))
    db_replacement = result.scalars().first()
    return db_replacement

@router.put("/{replacement_id}", response_model=ReplacementsRead)
async def update_replacement(replacement_id: int, replacement: ReplacementsUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Replacement).filter(Replacement.id == replacement_id))
    db_replacement = result.scalars().first()
    if db_replacement is None:
        raise HTTPException(status_code=404, detail="replacement not found")
    for var, value in vars(replacement).items():
        setattr(db_replacement, var, value) if value is not None else None
    await db.commit()
    await db.refresh(db_replacement)
    return db_replacement

@router.delete("/{replacement_id}", response_model=ReplacementsRead)
async def delete_replacement(replacement_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Replacement).filter(Replacement.id == replacement_id))
    replacement = result.scalars().first()
    if replacement is None:
        raise HTTPException(status_code=404, detail="replacement not found")
    await db.delete(replacement)
    await db.commit()
    return replacement
