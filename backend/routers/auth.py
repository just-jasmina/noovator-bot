from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..services.auth import verify_telegram_init_data, get_or_create_user, create_access_token, authenticate_expert
from ..services.xp_engine import process_daily_login
from ..schemas.user import TelegramInitData, TokenResponse, ExpertLoginRequest
from ..models.user import UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=TokenResponse)
async def auth_telegram(payload: TelegramInitData, db: AsyncSession = Depends(get_db)):
    """Validate Telegram initData and return JWT + registration status."""
    tg_user = verify_telegram_init_data(payload.init_data)
    if tg_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram initData signature"
        )

    user, is_new = await get_or_create_user(db, tg_user)

    if not is_new and user.status == "active":
        await process_daily_login(db, user)

    token = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        is_registered=bool(user.pnfl),
    )


@router.post("/expert/login", response_model=TokenResponse)
async def auth_expert(payload: ExpertLoginRequest, db: AsyncSession = Depends(get_db)):
    """Login for experts using username and password."""
    import traceback
    try:
        user = await authenticate_expert(db, payload.username, payload.password)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Noto'g'ri login yoki parol"
            )
        if str(user.role) not in ("expert", "moderator", "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu akkaunt expert huquqiga ega emas"
            )
        token = create_access_token(user.id)
        return TokenResponse(
            access_token=token,
            user_id=str(user.id),
            is_registered=True,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {traceback.format_exc()}")
