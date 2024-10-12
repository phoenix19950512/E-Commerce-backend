from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, any_, or_
from typing import List
from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.models.internal_product import Internal_Product
from app.models.scan_awb import Scan_awb
from app.models.team_member import Team_member
from app.schemas.scan_awb import Scan_awbCreate, Scan_awbRead, Scan_awbUpdate

router = APIRouter()

@router.post("/", response_model=Scan_awbRead)
async def create_scan_awb(scan_awb: Scan_awbCreate, db: AsyncSession = Depends(get_db)):
    db_scan_awb = Scan_awb(**scan_awb.dict())
    result = await db.execute(select(Scan_awb).where(Scan_awb.awb_number == db_scan_awb.awb_number))
    scan_awb = result.scalars().first()
    if scan_awb:
        return scan_awb
    db.add(db_scan_awb)
    await db.commit()
    await db.refresh(db_scan_awb)
    return db_scan_awb

@router.get('/count')
async def get_scan_awb_count(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.role == -1:
        raise HTTPException(status_code=401, detail="Authentication error")
    
    if user.role != 4:
        result = await db.execute(select(Team_member).where(Team_member.user == user.id))
        db_team = result.scalars().first()
        user_id = db_team.admin
    else:
        user_id = user.id
        
    result = await db.execute(select(Scan_awb).where(Scan_awb.user_id == user_id))
    scan_awbs = result.scalars().all()
    return len(scan_awbs)

@router.get("/", response_model=List[Scan_awbRead])
async def get_scan_awbs(
    page: int = Query(1, ge=1, description="Page number"),
    itmes_per_page: int = Query(50, ge=1, le=100, description="Number of items per page"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if user.role == -1:
        raise HTTPException(status_code=401, detail="Authentication error")
    
    if user.role != 4:
        result = await db.execute(select(Team_member).where(Team_member.user == user.id))
        db_team = result.scalars().first()
        user_id = db_team.admin
    else:
        user_id = user.id
        
    offset = (page - 1) * itmes_per_page
    result = await db.execute(select(Scan_awb).where(Scan_awb.user_id == user_id).offset(offset).limit(itmes_per_page))
    db_scan_awbs = result.scalars().all()
    if db_scan_awbs is None:
        raise HTTPException(status_code=404, detail="scan_awb not found")
    return db_scan_awbs

@router.get("/{scan_awb_id}", response_model=Scan_awbRead)
async def get_scan_awb(scan_awb_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.role == -1:
        raise HTTPException(status_code=401, detail="Authentication error")
    
    if user.role != 4:
        result = await db.execute(select(Team_member).where(Team_member.user == user.id))
        db_team = result.scalars().first()
        user_id = db_team.admin
    else:
        user_id = user.id
        
    result = await db.execute(select(Scan_awb).where(Scan_awb.id == scan_awb_id, Scan_awb.user_id == user_id))
    db_scan_awb = result.scalars().first()
    return db_scan_awb

@router.put("/{scan_awb_id}", response_model=Scan_awbRead)
async def update_scan_awb(scan_awb_id: int, scan_awb: Scan_awbUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.role == -1:
        raise HTTPException(status_code=401, detail="Authentication error")
    
    if user.role != 4:
        result = await db.execute(select(Team_member).where(Team_member.user == user.id))
        db_team = result.scalars().first()
        user_id = db_team.admin
    else:
        user_id = user.id
        
    result = await db.execute(select(Scan_awb).where(Scan_awb.id == scan_awb_id, Scan_awb.user_id == user_id))
    db_scan_awb = result.scalars().first()
    if db_scan_awb is None:
        raise HTTPException(status_code=404, detail="scan_awb not found")
    for var, value in vars(scan_awb).items():
        setattr(db_scan_awb, var, value) if value is not None else None
    await db.commit()
    await db.refresh(db_scan_awb)
    return db_scan_awb

@router.delete("/{scan_awb_id}", response_model=Scan_awbRead)
async def delete_scan_awb(scan_awb_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.role == -1:
        raise HTTPException(status_code=401, detail="Authentication error")
    
    if user.role != 4:
        result = await db.execute(select(Team_member).where(Team_member.user == user.id))
        db_team = result.scalars().first()
        user_id = db_team.admin
    else:
        user_id = user.id
        
    result = await db.execute(select(Scan_awb).where(Scan_awb.id == scan_awb_id, Scan_awb.user_id == user_id))
    scan_awb = result.scalars().first()
    if scan_awb is None:
        raise HTTPException(status_code=404, detail="scan_awb not found")
    await db.delete(scan_awb)
    await db.commit()
    return scan_awb
