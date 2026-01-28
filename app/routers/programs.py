from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import List

from app.database import get_session
from app.models.program import Program, ProgramCreate, ProgramResponse
from app.models.user import User
from app.routers.auth import require_admin

router = APIRouter(prefix="/api/programs", tags=["programs"])


@router.get("/", response_model=List[ProgramResponse])
async def list_programs(db: AsyncSession = Depends(get_session)):
    """List all programs (accessible to all authenticated users)"""
    result = await db.execute(select(Program).order_by(Program.name))
    programs = result.scalars().all()
    return programs


@router.post("/", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
async def create_program(
    program: ProgramCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Create a new program (admin only)"""
    db_program = Program(name=program.name)
    
    try:
        db.add(db_program)
        await db.commit()
        await db.refresh(db_program)
        return db_program
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Program with this name already exists"
        )


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_program(
    program_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Delete a program (admin only)"""
    result = await db.execute(select(Program).where(Program.id == program_id))
    program = result.scalar_one_or_none()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    await db.delete(program)
    await db.commit()
    return None
