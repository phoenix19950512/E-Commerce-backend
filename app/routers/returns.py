from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, any_
from typing import List
from app.database import get_db
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

@router.get("/", response_model=List[ReturnsRead])
async def get_returns(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Returns))
    db_returns = result.scalars().all()
    if db_returns is None:
        raise HTTPException(status_code=404, detail="return not found")
    return db_returns

@router.get("/replacement")
async def get_replacement(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Returns).filter(Returns.return_type == any_([1, 2])))
    db_replacements = result.scalars().all()
    return db_replacements

@router.put("/{return_id}", response_model=ReturnsRead)
async def update_return(return_id: int, returns: ReturnsUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Returns).filter(Returns.order_id == return_id))
    db_return = result.scalars().first()
    if db_return is None:
        raise HTTPException(status_code=404, detail="return not found")
    for var, value in vars(returns).items():
        setattr(db_return, var, value) if value else None
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
