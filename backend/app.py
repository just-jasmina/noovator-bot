from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from .config import settings
from .database import create_tables
from .routers import auth, users, projects, reviews, comments, leaderboard, mentorship, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await create_tables()
    except Exception as e:
        import logging
        logging.warning(f"create_tables skipped: {e}")
    try:
        await seed_xp_rules()
    except Exception as e:
        import logging
        logging.warning(f"seed_xp_rules skipped: {e}")
    yield


async def seed_xp_rules():
    """Insert default XP rules if not present."""
    from .database import async_session
    from .models.xp import XPRule
    from sqlalchemy import select

    DEFAULT_RULES = [
        ("profile_verified", 50, "Однократно при верификации профиля"),
        ("daily_login", 2, "Ежедневный вход (макс. 1 раз/сутки)"),
        ("streak_7days", 20, "Стрик 7 дней подряд"),
        ("comment_constructive", 5, "Конструктивный комментарий (50+ символов)"),
        ("project_submitted", 50, "Подача проекта на экспертизу"),
        ("project_approved", 200, "Проект прошёл Blind Review (≥2 Одобрить)"),
        ("project_pilot", 500, "Проект переведён в Пилот"),
        ("project_scaled", 1000, "Проект масштабирован на республику"),
        ("mentor_success", 1500, "Курируемый проект внедрён"),
    ]
    async with async_session() as session:
        for action, amount, desc in DEFAULT_RULES:
            existing = await session.execute(select(XPRule).where(XPRule.action == action))
            if not existing.scalar_one_or_none():
                session.add(XPRule(action=action, xp_amount=amount, description=desc))
        await session.commit()


app = FastAPI(
    title="Tibbiyot Novatorlari API",
    description="Unified digital platform for medical innovation — Ministry of Health, Uzbekistan",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = settings.API_PREFIX
app.include_router(auth.router, prefix=PREFIX)
app.include_router(users.router, prefix=PREFIX)
app.include_router(projects.router, prefix=PREFIX)
app.include_router(reviews.router, prefix=PREFIX)
app.include_router(comments.router, prefix=PREFIX)
app.include_router(leaderboard.router, prefix=PREFIX)
app.include_router(mentorship.router, prefix=PREFIX)
app.include_router(admin.router, prefix=PREFIX)

# Serve uploaded media files
os.makedirs("media", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Tibbiyot Novatorlari API"}
