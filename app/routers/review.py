from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewRead, ReviewUpdate

router = APIRouter()

@router.post("/", response_model=ReviewRead)
async def create_review(review: ReviewCreate, db: AsyncSession = Depends(get_db)):
    db_review = Review(**review.dict())
    db.add(db_review)
    await db.commit()
    db.refresh(db_review)
    return db_review

@router.get('/count')
async def get_reviews_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(func.count(Review.id))
    count = result.scalar()
    return count

@router.get("/", response_model=List[ReviewRead])
async def get_reviews(
    db: AsyncSession = Depends(get_db)
):
    
    result = await db.execute(select(Review))
    db_reviews = result.scalars().all()
    if db_reviews is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return db_reviews

@router.put("/{review_id}", response_model=ReviewRead)
async def update_review(review_id: int, review: ReviewUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Review).filter(Review.id == review_id))
    db_review = result.scalars().first()
    if db_review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    for var, value in vars(review).items():
        setattr(db_review, var, value) if value else None
    db.add(db_review)
    await db.commit()
    db.refresh(db_review)
    return db_review

@router.delete("/{review_id}", response_model=ReviewRead)
async def delete_review(review_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Review).filter(Review.id == review_id))
    review = result.scalars().first()
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    await db.delete(review)
    await db.commit()
    return review
