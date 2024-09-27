from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
from app.models.user import User
from app.routers.auth import get_current_user
from app.database import get_db
from app.models.warehouse import Warehouse
from app.schemas.warehouse import WarehouseCreate, WarehouseRead, WarehouseUpdate

router = APIRouter()

@router.post("/", response_model=WarehouseRead)
async def create_warehouse(warehouse: WarehouseCreate, db: AsyncSession = Depends(get_db)):
    db_warehouse = Warehouse(**warehouse.dict())
    db.add(db_warehouse)
    await db.commit()
    await db.refresh(db_warehouse)
    return db_warehouse

@router.get('/count')
async def get_warehouses_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(func.count(Warehouse.id))
    count = result.scalar()
    return count

@router.get("/", response_model=List[WarehouseRead])
async def get_warehouses(
    db: AsyncSession = Depends(get_db)
):
    
    result = await db.execute(select(Warehouse))
    db_warehouses = result.scalars().all()
    if db_warehouses is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return db_warehouses

@router.put("/{warehouse_id}", response_model=WarehouseRead)
async def update_warehouse(warehouse_id: int, warehouse: WarehouseUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Warehouse).filter(Warehouse.id == warehouse_id))
    db_warehouse = result.scalars().first()
    if db_warehouse is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    update_data = warehouse.dict(exclude_unset=True)  # Only update fields that are set
    for key, value in update_data.items():
        setattr(db_warehouse, key, value) if value is not None else None
    await db.commit()
    await db.refresh(db_warehouse)
    return db_warehouse

@router.delete("/{warehouse_id}", response_model=WarehouseRead)
async def delete_warehouse(warehouse_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Warehouse).filter(Warehouse.id == warehouse_id))
    warehouse = result.scalars().first()
    if warehouse is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    await db.delete(warehouse)
    await db.commit()
    return warehouse
