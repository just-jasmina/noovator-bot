from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
from pydantic import BaseModel, field_validator
from ..database import get_db
from ..middleware.auth import get_active_user
from ..models.user import User, UserRole
from ..models.project import Project, ProjectStatus
from ..models.review import Review, ReviewDecision
from ..services.smart_router import compute_majority_decision
from ..services.xp_engine import award_xp
from ..services.notifications import notify_user
from ..models.notification import NotificationType

router = APIRouter(prefix="/reviews", tags=["reviews"])


class ReviewSubmit(BaseModel):
    decision: ReviewDecision
    review_text: str
    checklist: List[str] | None = None

    @field_validator("review_text")
    @classmethod
    def validate_min_words(cls, v: str) -> str:
        if len(v.split()) < 150:
            raise ValueError("Review must be at least 150 words")
        return v


@router.get("/my", response_model=List[dict])
async def my_review_queue(
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in (UserRole.EXPERT, UserRole.ADMIN, UserRole.MODERATOR):
        raise HTTPException(status_code=403, detail="Experts only")

    # UUID-based experts (profiles table) have no integer FK in reviews yet — return empty
    try:
        int(str(user.id))
    except (ValueError, TypeError):
        return []

    result = await db.execute(
        select(Review).where(
            and_(Review.expert_id == user.id, Review.completed_at == None)
        )
    )
    reviews = result.scalars().all()
    output = []
    for r in reviews:
        proj = r.project
        output.append({
            "review_id": r.id,
            "project_id": r.project_id,
            "title": proj.title if proj else "—",
            "tags": [t.tag for t in proj.tags] if proj else [],
            "sla_deadline": r.sla_deadline,
            "is_overdue": r.is_overdue,
        })
    return output


@router.post("/{review_id}", response_model=dict)
async def submit_review(
    review_id: int,
    data: ReviewSubmit,
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Review).where(and_(Review.id == review_id, Review.expert_id == user.id))
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found or not assigned to you")
    if review.completed_at:
        raise HTTPException(status_code=400, detail="Already reviewed")

    review.decision = data.decision
    review.review_text = data.review_text
    if data.checklist:
        import json
        review.checklist = json.dumps(data.checklist)
    review.completed_at = datetime.now(timezone.utc)

    project = review.project
    project.review_count += 1
    await db.flush()

    # Check for majority
    majority = await compute_majority_decision(db, project.id)
    if majority == "approve":
        project.status = ProjectStatus.CROWDSOURCE
        await award_xp(db, project.author, "project_approved", "Project approved", project.id)
        await notify_user(project.author.telegram_id, NotificationType.REVIEW_VERDICT, verdict="✅ Tasdiqlandi / Одобрен")
    elif majority == "reject":
        project.status = ProjectStatus.REJECTED
        await notify_user(project.author.telegram_id, NotificationType.REVIEW_VERDICT, verdict="❌ Rad etildi / Отклонён")
    elif majority == "revision":
        project.status = ProjectStatus.REVISION
        await notify_user(project.author.telegram_id, NotificationType.REVIEW_VERDICT, verdict="🔄 Qayta ishlash / На доработку")

    await db.flush()
    return {"status": "ok", "majority": majority}
