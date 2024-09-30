from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.user import User
from app.routers.auth import get_current_user
from app.models.team_member import Team_member
from app.schemas.team_member import Team_memberCreate, Team_memberRead, Team_memberUpdate

router = APIRouter()

@router.post("/", response_model=Team_memberRead)
async def create_team_member(team_member: Team_memberCreate, admin: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if admin.role != 4:
        raise HTTPException(status_code=401, detail="Authentication error")
    db_team_member = Team_member(**team_member.dict())
    db_team_member.admin = admin.id
    db.add(db_team_member)
    await db.commit()
    await db.refresh(db_team_member)
    return db_team_member

@router.get('/count')
async def get_team_members_count(admin: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team_member).where(Team_member.admin == admin.id))
    db_members = result.scalars().all()
    return len(db_members)

@router.get("/")
async def get_team_members(
    admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    result = await db.execute(select(Team_member).where(Team_member.admin == admin.id))
    db_team = result.scalars().all()
    if db_team is None:
        raise HTTPException(status_code=404, detail="Team_member not found")
    
    user_data = []
    for member in db_team:
        result = await db.execute(select(User).where(User.id == member.user))
        db_user = result.scalars().first()
        user_data.append(db_user)
    return user_data

@router.put("/")
async def update_team_member(team_member: Team_memberUpdate, admin: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = team_member.user
    role = team_member.role
    result = await db.execute(select(Team_member).where(Team_member.user == user, Team_member.admin == admin.id))
    db_team_member = result.scalars().first()
    if db_team_member is None:
        raise HTTPException(status_code=404, detail="Team_member not found")

    result = await db.execute(select(User).where(User.id == user))
    db_user = result.scalars().first()
    db_user.role = role
    
    db.add(db_team_member)
    await db.commit()
    await db.refresh(db_team_member)
    return db_team_member

@router.delete("/", response_model=Team_memberRead)
async def delete_team_member(user: int, admin: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team_member).where(Team_member.admin == admin.id, Team_member.user == user))
    team_member = result.scalars().first()
    if team_member is None:
        raise HTTPException(status_code=404, detail="Team_member not found")
    await db.delete(team_member)
    await db.commit()
    return team_member
