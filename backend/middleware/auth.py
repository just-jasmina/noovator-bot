from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..services.auth import decode_access_token
from ..models.user import User, UserRole, UserStatus

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    from sqlalchemy import text as sa_text
    token = credentials.credentials
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Try integer id (users table)
    user = None
    try:
        int_id = int(user_id)
        result = await db.execute(select(User).where(User.id == int_id))
        user = result.scalar_one_or_none()
    except ValueError:
        pass

    # Fallback: UUID from profiles table (Supabase-native experts)
    if user is None:
        row = await db.execute(
            sa_text("SELECT id, role, status, expert_username, expert_tags FROM profiles WHERE id = :uid LIMIT 1"),
            {"uid": user_id},
        )
        profile = row.mappings().first()
        if profile:
            user = User()
            user.id = profile["id"]
            user.role = profile["role"]
            user.status = profile.get("status", "active")
            user.expert_username = profile.get("expert_username")
            user.expert_tags = profile.get("expert_tags")

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.status == UserStatus.BANNED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account banned")
    return user


async def get_active_user(user: User = Depends(get_current_user)) -> User:
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not verified yet"
        )
    return user


def require_role(*roles: UserRole):
    async def checker(user: User = Depends(get_active_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user
    return checker
