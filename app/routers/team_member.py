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
async def create_team_member(team_member: Team_memberCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    db_team_member = Team_member(**team_member.dict())
    db_team_member.user_id = user.id
    db.add(db_team_member)
    await db.commit()
    await db.refresh(db_team_member)
    return db_team_member

@router.get('/count')
async def get_team_members_count(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team_member).where(Team_member.user_id == user.id))
    db_team_member = result.scalars().first()
    members = db_team_member.member_id
    return len(members)

@router.get("/")
async def get_team_members(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    result = await db.execute(select(Team_member).where(Team_member.user_id == user.id))
    db_team_members = result.scalars().first()
    if db_team_members is None:
        raise HTTPException(status_code=404, detail="Team_member not found")
    member_list = db_team_members.member_id
    user_data = []
    for member in member_list:
        result = await db.execute(select(User).where(User.id == member))
        db_user = result.scalars().first()
        user_data.append(db_user)
    return user_data

@router.put("/{team_member_id}")
async def update_team_member(team_member_id: int, team_member: Team_memberUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team_member).filter(Team_member.id == team_member_id, Team_member.user_id == user.id))
    db_team_member = result.scalars().first()
    if db_team_member is None:
        raise HTTPException(status_code=404, detail="Team_member not found")
    
    db_team_member.member_id = team_member.member_id
    role = team_member.role
    
    users = team_member.member_id
    for i in range(len(users)):
        result = await db.execute(select(User).where(User.id == users[i]))
        db_user = result.scalars().first()
        db_user.role = role[i]
    
    db.add(db_team_member)
    await db.commit()
    await db.refresh(db_user)
    await db.refresh(db_team_member)
    return db_team_member

@router.delete("/{team_member_id}", response_model=Team_memberRead)
async def delete_team_member(team_member_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team_member).filter(Team_member.id == team_member_id, Team_member.user_id == user.id))
    team_member = result.scalars().first()
    if team_member is None:
        raise HTTPException(status_code=404, detail="Team_member not found")
    await db.delete(team_member)
    await db.commit()
    return team_member
