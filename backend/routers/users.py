import aiofiles
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..middleware.auth import get_current_user, get_active_user
from ..models.user import User, UserStatus
from ..models.xp import XPRule
from ..schemas.user import UserFullProfile, UserPublicProfile, UserRegistrationStep1, UserProfileUpdate
from ..services.xp_engine import award_xp
from ..services.notifications import notify_user
from ..models.notification import NotificationType

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserFullProfile)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserFullProfile)
async def update_profile(
    data: UserProfileUpdate,
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.flush()
    return user


@router.post("/register", response_model=UserFullProfile)
async def register_user(
    data: UserRegistrationStep1,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.pnfl:
        raise HTTPException(status_code=400, detail="Already registered")

    # Check PNFL uniqueness
    existing = await db.execute(
        select(User).where(User.pnfl == data.pnfl, User.id != user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="PNFL already registered")

    for field, value in data.model_dump().items():
        setattr(user, field, value)
    user.status = UserStatus.PENDING
    await db.flush()
    return user


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")
    # In production: upload to S3 and return URL
    filename = f"avatars/{user.id}_{file.filename}"
    user.avatar_url = f"/media/{filename}"
    await db.flush()
    return {"avatar_url": user.avatar_url}


@router.get("/{user_id}", response_model=UserPublicProfile)
async def get_user_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
