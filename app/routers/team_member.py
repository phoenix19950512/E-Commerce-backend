from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.team_member import Team_member
from app.schemas.team_member import Team_memberCreate, Team_memberRead, Team_memberUpdate

router = APIRouter()

@router.post("/", response_model=Team_memberRead)
async def create_team_member(team_member: Team_memberCreate, db: AsyncSession = Depends(get_db)):
    db_team_member = Team_member(**team_member.dict())
    db.add(db_team_member)
    await db.commit()
    await db.refresh(db_team_member)
    return db_team_member

@router.get('/count')
async def get_team_members_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(func.count(Team_member.id))
    count = result.scalar()
    return count

@router.get("/", response_model=List[Team_memberRead])
async def get_team_members(
    db: AsyncSession = Depends(get_db)
):
    
    result = await db.execute(select(Team_member))
    db_team_members = result.scalars().all()
    if db_team_members is None:
        raise HTTPException(status_code=404, detail="Team_member not found")
    return db_team_members

@router.put("/{team_member_id}", response_model=Team_memberRead)
async def update_team_member(team_member_id: int, team_member: Team_memberUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team_member).filter(Team_member.id == team_member_id))
    db_team_member = result.scalars().first()
    if db_team_member is None:
        raise HTTPException(status_code=404, detail="Team_member not found")
    for var, value in vars(team_member).items():
        setattr(db_team_member, var, value) if value else None
    db.add(db_team_member)
    await db.commit()
    await db.refresh(db_team_member)
    return db_team_member

@router.delete("/{team_member_id}", response_model=Team_memberRead)
async def delete_team_member(team_member_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team_member).filter(Team_member.id == team_member_id))
    team_member = result.scalars().first()
    if team_member is None:
        raise HTTPException(status_code=404, detail="Team_member not found")
    await db.delete(team_member)
    await db.commit()
    return team_member
