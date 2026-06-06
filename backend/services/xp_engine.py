from datetime import datetime, date, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from ..models.user import User
from ..models.xp import XPTransaction, XPRule


# Default XP values (overridable via xp_rules table)
DEFAULT_XP_RULES = {
    "profile_verified": 50,
    "daily_login": 2,
    "streak_7days": 20,
    "comment_constructive": 5,
    "project_submitted": 50,
    "project_approved": 200,
    "project_pilot": 500,
    "project_scaled": 1000,
    "mentor_success": 1500,
}


async def get_xp_amount(db: AsyncSession, action: str) -> int:
    result = await db.execute(
        select(XPRule).where(and_(XPRule.action == action, XPRule.is_active == True))
    )
    rule = result.scalar_one_or_none()
    return rule.xp_amount if rule else DEFAULT_XP_RULES.get(action, 0)


async def award_xp(
    db: AsyncSession,
    user: User,
    action: str,
    description: str = "",
    reference_id: int | None = None,
    is_seasonal: bool = True,
) -> int:
    """Award XP to user, returns amount awarded."""
    amount = await get_xp_amount(db, action)
    if amount == 0:
        return 0

    tx = XPTransaction(
        user_id=user.id,
        amount=amount,
        action=action,
        description=description,
        reference_id=reference_id,
        is_seasonal=is_seasonal,
    )
    db.add(tx)

    user.global_xp += amount
    if is_seasonal:
        user.season_xp += amount

    await db.flush()
    return amount


async def process_daily_login(db: AsyncSession, user: User) -> int:
    """Handle daily login XP + streak. Returns total XP awarded."""
    today = date.today()
    if user.last_streak_date == today:
        return 0

    total_xp = await award_xp(db, user, "daily_login", "Daily login bonus")

    yesterday = date.fromordinal(today.toordinal() - 1)
    if user.last_streak_date == yesterday:
        user.streak_days += 1
    else:
        user.streak_days = 1

    user.last_streak_date = today
    user.last_active = datetime.now(timezone.utc)

    if user.streak_days > 0 and user.streak_days % 7 == 0:
        total_xp += await award_xp(db, user, "streak_7days", f"{user.streak_days}-day streak bonus")

    await db.flush()
    return total_xp


async def reset_seasonal_xp(db: AsyncSession):
    """CRON: reset season_xp for all users at start of quarter."""
    from sqlalchemy import update
    await db.execute(update(User).values(season_xp=0))
    await db.flush()
