from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.courier import Courier
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.courier import CouriersCreate, CouriersRead, CouriersUpdate

router = APIRouter()

@router.get("/", response_model=List[CouriersRead])
async def get_couriers(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    result = await db.execute(select(Courier).where(Courier.user_id == user.id))
    db_couriers = result.scalars().all()
    if db_couriers is None:
        raise HTTPException(status_code=404, detail="couriers not found")
    return db_couriers

