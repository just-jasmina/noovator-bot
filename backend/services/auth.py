import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote, parse_qsl
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..config import settings
from ..models.user import User, UserRole

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_telegram_init_data(init_data: str) -> dict | None:
    """
    Verify Telegram initData signature (HMAC-SHA256).
    Returns parsed user dict or None if invalid.
    """
    parsed = dict(parse_qsl(unquote(init_data), keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        settings.BOT_TOKEN.encode(),
        hashlib.sha256,
    ).digest()

    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    # Check auth_date freshness (24 hours)
    auth_date = int(parsed.get("auth_date", 0))
    if datetime.now(timezone.utc).timestamp() - auth_date > 86400:
        return None

    user_data = json.loads(parsed.get("user", "{}"))
    return user_data


def create_access_token(user_id) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload["sub"]  # str — works for both int and UUID
    except (JWTError, KeyError):
        return None


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


async def authenticate_expert(db: AsyncSession, username: str, password: str) -> User | None:
    from sqlalchemy import text
    # Query profiles table directly (Supabase)
    try:
        row = await db.execute(
            text("SELECT id, expert_password_hash, role, status FROM profiles WHERE expert_username = :u LIMIT 1"),
            {"u": username},
        )
        profile = row.mappings().first()
    except Exception:
        profile = None

    if profile and profile["expert_password_hash"] and verify_password(password, profile["expert_password_hash"]):
        fake_user = User()
        fake_user.id = profile["id"]
        fake_user.role = profile["role"]
        fake_user.status = profile.get("status", "active")
        fake_user.expert_username = username
        return fake_user

    # Fallback: try users table
    try:
        result = await db.execute(select(User).where(User.expert_username == username))
        user = result.scalar_one_or_none()
        if user and user.expert_password_hash and verify_password(password, user.expert_password_hash):
            return user
    except Exception:
        pass

    return None


async def get_or_create_user(db: AsyncSession, tg_user: dict) -> tuple[User, bool]:
    """Supabase-native: find or create a profile row by telegram_id. Returns (user, is_new)."""
    from sqlalchemy import text as sa_text
    telegram_id = tg_user["id"]

    row = await db.execute(
        sa_text("SELECT id, role, status, pnfl, full_name FROM profiles WHERE telegram_id = :tid LIMIT 1"),
        {"tid": telegram_id},
    )
    profile = row.mappings().first()
    is_new = profile is None

    if is_new:
        full_name = " ".join(
            x for x in [tg_user.get("first_name"), tg_user.get("last_name")] if x
        ).strip()
        ins = await db.execute(
            sa_text("""
                INSERT INTO profiles (telegram_id, full_name, role, status, league,
                                      season_xp, global_xp, streak_days)
                VALUES (:tid, :fn, 'user', 'active', 'novice', 0, 0, 0)
                RETURNING id, role, status, pnfl, full_name
            """),
            {"tid": telegram_id, "fn": full_name},
        )
        profile = ins.mappings().first()

    user = User()
    user.id = profile["id"]
    user.role = profile["role"]
    user.status = profile["status"]
    user.pnfl = profile.get("pnfl")
    return user, is_new
