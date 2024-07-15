from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.notifications import Notification
from app.database import get_db
from app.schemas.notifications import NotificationCreate, NotificationUpdate, NotificationRead
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging
from pydantic import ValidationError

async def create_notification(db: AsyncSession, notifications: NotificationCreate):
    db_notification = Notification(**notifications.dict())
    db.add(db_notification)
    await db.commit()
    await db.refresh(db_notification)
    return {"msg": "success"}

async def get_notification(db: AsyncSession, notification_id: int):
    result = await db.execute(select(Notification).filter(Notification.id == notification_id))
    return result.scalars().first()

async def get_notifications(db: AsyncSession):
    result = await db.execute(select(Notification))
    return result.scalars().all()

async def update_notification(db: AsyncSession, notification_id: int, notifications: NotificationUpdate):
    db_notification = await get_notification(db, notification_id)
    if db_notification is None:
        return None
    for key, value in notifications.dict().items():
        setattr(db_notification, key, value)
    await db.commit()
    await db.refresh(db_notification)
    return db_notification

async def delete_notification(db: AsyncSession, notification_id: int):
    db_notification = await get_notification(db, notification_id)
    if db_notification is None:
        return None
    await db.delete(db_notification)
    await db.commit()
    return db_notification

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_new_notification(notifications: NotificationCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await create_notification(db, notifications)
    except ValidationError as e:
        logging.error(f"Validation error: {e.errors()}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())
    except Exception as e:
        logging.error(f"Error creating notifications: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

@router.get("/", response_model=List[NotificationRead])
async def read_notifications(db: AsyncSession = Depends(get_db)):
    return await get_notifications(db)

@router.get("/{notification_id}", response_model=NotificationRead)
async def read_notification(notification_id: int, db: AsyncSession = Depends(get_db)):
    notifications = await get_notification(db, notification_id)
    if notifications is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notifications

@router.put("/{notification_id}", response_model=NotificationRead)
async def update_existing_notification(notification_id: int, notifications: NotificationUpdate, db: AsyncSession = Depends(get_db)):
    updated_notification = await update_notification(db, notification_id, notifications)
    if updated_notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return updated_notification

@router.delete("/{notification_id}")
async def delete_existing_notification(notification_id: int, db: AsyncSession = Depends(get_db)):
    deleted_notification = await delete_notification(db, notification_id)
    if deleted_notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"msg": "success"}