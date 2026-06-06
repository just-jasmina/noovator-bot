"""Supabase-native user/profile endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from ..database import get_db
from ..middleware.auth import get_current_user, get_active_user
from ..models.user import User

router = APIRouter(prefix="/users", tags=["users"])


def _profile_dict(r: dict) -> dict:
    return {
        "id": str(r["id"]),
        "telegram_id": r.get("telegram_id"),
        "first_name": (r.get("full_name") or "").split(" ")[0] if r.get("full_name") else None,
        "last_name": " ".join((r.get("full_name") or "").split(" ")[1:]) or None,
        "full_name": r.get("full_name"),
        "role": r.get("role") or "user",
        "status": r.get("status") or "active",
        "league": r.get("league") or "novice",
        "season_xp": r.get("season_xp") or 0,
        "global_xp": r.get("global_xp") or 0,
        "streak_days": r.get("streak_days") or 0,
        "pnfl": r.get("pnfl"),
        "phone": r.get("phone"),
        "workplace": r.get("workplace"),
        "expert_tags": ", ".join(r.get("expert_tags") or []) if r.get("expert_tags") else None,
        "language": "uz",
        "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
    }


async def _load_profile(db: AsyncSession, user_id) -> dict | None:
    row = await db.execute(
        text("""SELECT id, telegram_id, full_name, role, status, league,
                       season_xp, global_xp, streak_days, pnfl, phone, workplace,
                       expert_tags, created_at
                FROM profiles WHERE id = :uid LIMIT 1"""),
        {"uid": str(user_id)},
    )
    r = row.mappings().first()
    return _profile_dict(dict(r)) if r else None


@router.get("/me", response_model=dict)
async def get_me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    profile = await _load_profile(db, user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


class ProfileUpdate(BaseModel):
    workplace: Optional[str] = None
    phone: Optional[str] = None


@router.put("/me", response_model=dict)
async def update_profile(
    data: ProfileUpdate,
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    fields = data.model_dump(exclude_unset=True)
    if fields:
        sets = ", ".join(f"{k} = :{k}" for k in fields)
        fields["uid"] = str(user.id)
        await db.execute(text(f"UPDATE profiles SET {sets} WHERE id = :uid"), fields)
    return await _load_profile(db, user.id)


class RegistrationData(BaseModel):
    pnfl: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    workplace: Optional[str] = None


@router.post("/register", response_model=dict)
async def register_user(
    data: RegistrationData,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    full_name = f"{data.first_name} {data.last_name}".strip()
    await db.execute(
        text("""UPDATE profiles
                SET pnfl = :pnfl, full_name = :fn, phone = :phone,
                    workplace = :wp, status = 'active'
                WHERE id = :uid"""),
        {"pnfl": data.pnfl, "fn": full_name, "phone": data.phone,
         "wp": data.workplace, "uid": str(user.id)},
    )
    return await _load_profile(db, user.id)


@router.get("/{user_id}", response_model=dict)
async def get_user_profile(user_id: str, db: AsyncSession = Depends(get_db)):
    profile = await _load_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile
