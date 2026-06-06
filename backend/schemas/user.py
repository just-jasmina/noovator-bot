from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import date, datetime
from ..models.user import UserRole, UserLeague, UserStatus, UserGender, UserAccountStatus


class TelegramInitData(BaseModel):
    init_data: str


class ExpertLoginRequest(BaseModel):
    username: str
    password: str


class ExpertCreateRequest(BaseModel):
    user_id: int
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    is_registered: bool


class UserRegistrationStep1(BaseModel):
    pnfl: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    phone: str
    email: EmailStr
    birth_date: date
    gender: UserGender
    region_type: str
    region: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    account_status: UserAccountStatus
    diploma_specialty: str
    current_specialty: Optional[str] = None
    workplace: Optional[str] = None
    study_place: Optional[str] = None

    @field_validator("pnfl")
    @classmethod
    def validate_pnfl(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 14:
            raise ValueError("PNFL must be exactly 14 digits")
        return v


class UserProfileUpdate(BaseModel):
    current_specialty: Optional[str] = None
    workplace: Optional[str] = None
    language: Optional[str] = None
    phone: Optional[str] = None


class UserPublicProfile(BaseModel):
    id: int
    telegram_username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    league: UserLeague
    role: UserRole
    season_xp: int
    global_xp: int
    region: Optional[str] = None
    current_specialty: Optional[str] = None
    workplace: Optional[str] = None
    streak_days: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserFullProfile(UserPublicProfile):
    pnfl: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[UserGender] = None
    status: UserStatus
    account_status: Optional[UserAccountStatus] = None
    diploma_specialty: Optional[str] = None
    study_place: Optional[str] = None
    language: str
    streak_days: int
    expert_tags: Optional[str] = None


class LeaderboardEntry(BaseModel):
    rank: int
    user: UserPublicProfile
    season_xp: int
    global_xp: int
