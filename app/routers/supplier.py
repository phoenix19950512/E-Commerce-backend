from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate

router = APIRouter()

@router.post("/", response_model=SupplierRead)
async def create_supplier(product: SupplierCreate, db: AsyncSession = Depends(get_db)):
    db_supplier = Supplier(**product.dict())
    db.add(db_supplier)
    await db.commit()
    await db.refresh(db_supplier)
    return db_supplier

@router.get('/count')
async def get_suppliers_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(func.count(Supplier.id))
    count = result.scalar()
    return count

@router.get("/{supplier_id}", response_model=SupplierRead)
async def read_supplier(supplier_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Supplier).filter(Supplier.id == supplier_id))
    supplier = result.scalars().first()
    if supplier is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return supplier

@router.get("/", response_model=List[SupplierRead])
async def get_products(
    supplier_ids: str = Query(None),
    page: int = Query(1, ge=1, description="Page number"),
    items_per_page: int = Query(50, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_db)
):
    
    offset = (page - 1) * items_per_page
    if supplier_ids:
        supplier_id_list = [int(id.strip()) for id  in supplier_ids.split(",")]
        result = await db.execute(select(Supplier).filter(Supplier.id.in_(supplier_id_list)).offset(offset).limit(items_per_page))
    else:
        result = await db.execute(select(Supplier).offset(offset).limit(items_per_page))
    db_suppliers = result.scalars().all()
    if db_suppliers is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return db_suppliers

@router.get("/{supplier_id}", response_model=SupplierRead)
async def update_product(supplier_id: int, product: SupplierUpdate, db: AsyncSession = Depends(get_db)):
    db_supplier = await db.execute(select(Supplier).filter(Supplier.id == supplier_id)).scalars().first()
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    for var, value in vars(product).items():
        setattr(db_supplier, var, value) if value else None
    await db.commit()
    await db.refresh(db_supplier)
    return db_supplier
