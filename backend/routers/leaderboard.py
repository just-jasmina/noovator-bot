from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from ..database import get_db
from ..models.user import User, UserLeague, UserStatus

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

LEAGUE_ORDER = [UserLeague.INNOVATOR, UserLeague.PROFESSIONAL, UserLeague.AMATEUR, UserLeague.NOVICE]
LEAGUE_LABELS = {
    UserLeague.NOVICE: {"uz": "Yangi Boshlovchi", "ru": "Новичок"},
    UserLeague.AMATEUR: {"uz": "Havaskor", "ru": "Любитель"},
    UserLeague.PROFESSIONAL: {"uz": "Professional", "ru": "Профессионал"},
    UserLeague.INNOVATOR: {"uz": "Novator", "ru": "Новатор"},
}


@router.get("")
async def get_leaderboard(
    league: str = Query("all"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(User).where(User.status == UserStatus.ACTIVE)

    if league != "all":
        query = query.where(User.league == league)

    query = query.order_by(desc(User.season_xp)).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    users = result.scalars().all()

    entries = []
    for i, u in enumerate(users, start=(page - 1) * size + 1):
        entries.append({
            "rank": i,
            "user_id": u.id,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "avatar_url": u.avatar_url,
            "league": u.league,
            "season_xp": u.season_xp,
            "global_xp": u.global_xp,
            "streak_days": u.streak_days,
            "region": u.region,
        })

    return {
        "league": league,
        "entries": entries,
        "leagues": [
            {
                "key": lg,
                "label_uz": LEAGUE_LABELS[lg]["uz"],
                "label_ru": LEAGUE_LABELS[lg]["ru"],
            }
            for lg in LEAGUE_ORDER
        ],
    }


@router.get("/my-rank")
async def my_rank(
    league: str = Query("all"),
    db: AsyncSession = Depends(get_db),
    user_id: int = Query(...),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"rank": None}

    query = select(User).where(
        User.status == UserStatus.ACTIVE,
        User.season_xp > user.season_xp,
    )
    if league != "all":
        query = query.where(User.league == league)

    count_result = await db.execute(
        select(User).where(
            User.status == UserStatus.ACTIVE,
            User.season_xp > user.season_xp,
        )
    )
    rank = len(count_result.scalars().all()) + 1
    return {"rank": rank, "season_xp": user.season_xp, "global_xp": user.global_xp}
