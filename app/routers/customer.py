from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.customer import Customers
from app.schemas.customer import CustomersCreate, CustomersRead, CustomersUpdate

router = APIRouter()

@router.post("/", response_model=CustomersRead)
async def create_customers_(customers: CustomersCreate, db: AsyncSession = Depends(get_db)):
    db_customers = Customers(**customers.dict())
    db.add(db_customers)
    await db.commit()
    await db.refresh(db_customers)
    return db_customers

@router.get('/count')
async def get_customers_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(func.count(Customers.id))
    count = result.scalar()
    return count

@router.get("/", response_model=List[CustomersRead])
async def get_customers(
    page: int = Query(1, ge=1, description="Page number"),
    items_per_page: int = Query(50, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_db)
):
    
    offset = (page - 1) * items_per_page
    result = await db.execute(select(Customers).offset(offset).limit(items_per_page))
    db_customerss = result.scalars().all()
    if db_customerss is None:
        raise HTTPException(status_code=404, detail="customers not found")
    return db_customerss

@router.put("/{customer_id}", response_model=CustomersRead)
async def update_customers(customer_id: int, customer: CustomersUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customers).filter(Customers.id == customer_id))
    db_customers = result.scalars().first()
    if db_customers is None:
        raise HTTPException(status_code=404, detail="customers not found")
    for var, value in vars(customer).items():
        setattr(db_customers, var, value) if value is not None else None
    await db.commit()
    await db.refresh(db_customers)
    return db_customers

@router.delete("/{customers_id}", response_model=CustomersRead)
async def delete_customers(customers_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customers).filter(Customers.id == customers_id))
    customers = result.scalars().first()
    if customers is None:
        raise HTTPException(status_code=404, detail="customers not found")
    await db.delete(customers)
    await db.commit()
    return customers
