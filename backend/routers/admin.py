from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from pydantic import BaseModel
from typing import Optional, List
from ..database import get_db
from ..middleware.auth import require_role
from ..models.user import User, UserRole, UserStatus, UserLeague
from ..models.project import Project, ProjectStatus
from ..models.review import Review
from ..models.xp import XPRule, XPTransaction
from ..models.notification import NotificationType
from ..services.notifications import notify_user
from ..services.xp_engine import award_xp
from ..services.auth import hash_password
from ..schemas.user import ExpertCreateRequest

router = APIRouter(prefix="/admin", tags=["admin"])

admin_only = require_role(UserRole.ADMIN)
mod_or_admin = require_role(UserRole.ADMIN, UserRole.MODERATOR)


@router.get("/dashboard")
async def dashboard(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(mod_or_admin),
):
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    active_users = (await db.execute(select(func.count(User.id)).where(User.status == UserStatus.ACTIVE))).scalar()
    pending_users = (await db.execute(select(func.count(User.id)).where(User.status == UserStatus.PENDING))).scalar()
    total_projects = (await db.execute(select(func.count(Project.id)))).scalar()
    in_review = (await db.execute(select(func.count(Project.id)).where(Project.status == ProjectStatus.REVIEW))).scalar()
    in_pilot = (await db.execute(select(func.count(Project.id)).where(Project.status == ProjectStatus.PILOT))).scalar()
    scaled = (await db.execute(select(func.count(Project.id)).where(Project.status == ProjectStatus.SCALED))).scalar()

    league_counts = {}
    for league in UserLeague:
        count = (await db.execute(
            select(func.count(User.id)).where(User.league == league, User.status == UserStatus.ACTIVE)
        )).scalar()
        league_counts[league.value] = count

    return {
        "users": {"total": total_users, "active": active_users, "pending": pending_users},
        "projects": {"total": total_projects, "in_review": in_review, "in_pilot": in_pilot, "scaled": scaled},
        "leagues": league_counts,
    }


@router.get("/pending-users")
async def pending_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(mod_or_admin),
    page: int = Query(1, ge=1),
):
    result = await db.execute(
        select(User).where(User.status == UserStatus.PENDING)
        .order_by(User.created_at)
        .offset((page - 1) * 20).limit(20)
    )
    users = result.scalars().all()
    return [
        {
            "id": u.id, "telegram_id": u.telegram_id, "first_name": u.first_name,
            "last_name": u.last_name, "pnfl": u.pnfl, "email": u.email,
            "phone": u.phone, "region_type": u.region_type, "diploma_url": u.diploma_url,
            "account_status": u.account_status, "created_at": u.created_at,
        }
        for u in users
    ]


class VerifyUserAction(BaseModel):
    action: str  # approve / reject
    reason: Optional[str] = None
    region: Optional[str] = None
    region_type: Optional[str] = None


@router.post("/users/{user_id}/verify")
async def verify_user(
    user_id: int,
    data: VerifyUserAction,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(mod_or_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.action == "approve":
        user.status = UserStatus.ACTIVE
        if data.region:
            user.region = data.region
        if data.region_type:
            user.region_type = data.region_type
        await award_xp(db, user, "profile_verified", "Profile verified by moderator")
        await notify_user(user.telegram_id, NotificationType.VERIFICATION_APPROVED)
    elif data.action == "reject":
        user.status = UserStatus.REJECTED
        await notify_user(user.telegram_id, NotificationType.VERIFICATION_REJECTED, reason=data.reason or "")

    await db.flush()
    return {"status": user.status}


class AssignExpertRole(BaseModel):
    tags: List[str]


@router.post("/users/{user_id}/make-expert")
async def make_expert(
    user_id: int,
    data: AssignExpertRole,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = UserRole.EXPERT
    user.expert_tags = ",".join(data.tags[:3])
    await db.flush()
    return {"role": user.role, "tags": user.expert_tags}


@router.post("/experts/set-credentials")
async def set_expert_credentials(
    data: ExpertCreateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
):
    """Set or update username/password for an expert user."""
    result = await db.execute(select(User).where(User.id == data.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role not in (UserRole.EXPERT, UserRole.MODERATOR, UserRole.ADMIN):
        raise HTTPException(status_code=400, detail="Foydalanuvchi expert emas")

    # Check username uniqueness
    existing = await db.execute(
        select(User).where(User.expert_username == data.username, User.id != data.user_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu username band")

    user.expert_username = data.username
    user.expert_password_hash = hash_password(data.password)
    await db.flush()
    return {"user_id": user.id, "username": user.expert_username, "status": "credentials set"}


@router.get("/xp-rules")
async def get_xp_rules(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
):
    result = await db.execute(select(XPRule))
    rules = result.scalars().all()
    return [{"id": r.id, "action": r.action, "xp_amount": r.xp_amount, "description": r.description} for r in rules]


class XPRuleUpdate(BaseModel):
    xp_amount: int


@router.put("/xp-rules/{rule_id}")
async def update_xp_rule(
    rule_id: int,
    data: XPRuleUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
):
    result = await db.execute(select(XPRule).where(XPRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.xp_amount = data.xp_amount
    await db.flush()
    return {"action": rule.action, "xp_amount": rule.xp_amount}


@router.post("/projects/{project_id}/pilot")
async def send_to_pilot(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.status = ProjectStatus.PILOT
    await award_xp(db, project.author, "project_pilot", "Project moved to Pilot", project.id)
    await notify_user(project.author.telegram_id, NotificationType.PROJECT_TO_PILOT)
    await db.flush()
    return {"status": "pilot"}


@router.post("/projects/{project_id}/scale")
async def scale_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.status = ProjectStatus.SCALED
    await award_xp(db, project.author, "project_scaled", "Project scaled nationally", project.id)
    await notify_user(project.author.telegram_id, NotificationType.PROJECT_SCALED)

    # Mentor bonus if any
    if project.mentorship and project.mentorship.status == MentorshipStatus.ACTIVE:
        mentor = project.mentorship.mentor
        await award_xp(db, mentor, "mentor_success", "Mentee project scaled", project.id, is_seasonal=False)

    await db.flush()
    return {"status": "scaled"}
