"""Supabase-native expert review endpoints (UUID schema, raw SQL)."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, field_validator
from typing import List, Optional

from ..database import get_db
from ..middleware.auth import get_active_user
from ..models.user import User, UserRole
from ..services.tag_routing import tag_label, compute_and_apply_decision

router = APIRouter(prefix="/reviews", tags=["reviews"])


class ReviewSubmit(BaseModel):
    decision: str
    review_text: str
    checklist: Optional[List[str]] = None

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v: str) -> str:
        if v not in ("approve", "reject", "revision"):
            raise ValueError("Invalid decision")
        return v

    @field_validator("review_text")
    @classmethod
    def validate_min_words(cls, v: str) -> str:
        if len(v.split()) < 150:
            raise ValueError("Review must be at least 150 words")
        return v


def _is_expert(user: User) -> bool:
    return str(user.role) in ("expert", "moderator", "admin")


@router.get("/my", response_model=List[dict])
async def my_review_queue(
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Pending reviews assigned to the current expert."""
    if not _is_expert(user):
        raise HTTPException(status_code=403, detail="Experts only")

    rows = await db.execute(
        text("""
            SELECT r.id AS review_id, r.sla_deadline,
                   pr.id AS project_id, pr.title, pr.pitch, pr.tags, pr.status
            FROM reviews r
            JOIN projects pr ON pr.id = r.project_id
            WHERE r.expert_id = :eid AND r.reviewed_at IS NULL
            ORDER BY r.sla_deadline ASC NULLS LAST
        """),
        {"eid": str(user.id)},
    )
    now = datetime.now(timezone.utc)
    out = []
    for r in rows.mappings().all():
        sla = r["sla_deadline"]
        out.append({
            "review_id": str(r["review_id"]),
            "project_id": str(r["project_id"]),
            "title": r["title"],
            "pitch": r["pitch"],
            "tags": list(r["tags"] or []),
            "tag_labels": [tag_label(t) for t in (r["tags"] or [])],
            "sla_deadline": sla.isoformat() if sla else None,
            "is_overdue": bool(sla and sla < now),
        })
    return out


@router.get("/{review_id}", response_model=dict)
async def get_review(
    review_id: str,
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Full project detail for a review (blind — author hidden)."""
    if not _is_expert(user):
        raise HTTPException(status_code=403, detail="Experts only")

    row = await db.execute(
        text("""
            SELECT r.id AS review_id, r.decision, r.review_text, r.reviewed_at, r.sla_deadline,
                   pr.id AS project_id, pr.title, pr.pitch, pr.problem, pr.solution,
                   pr.audience, pr.kpis, pr.effect, pr.cost_range, pr.budget_use,
                   pr.timeline, pr.tags, pr.status
            FROM reviews r
            JOIN projects pr ON pr.id = r.project_id
            WHERE r.id = :rid AND r.expert_id = :eid
            LIMIT 1
        """),
        {"rid": review_id, "eid": str(user.id)},
    )
    r = row.mappings().first()
    if not r:
        raise HTTPException(status_code=404, detail="Review not found")

    return {
        "review_id": str(r["review_id"]),
        "project_id": str(r["project_id"]),
        "title": r["title"],
        "pitch": r["pitch"],
        "problem": r["problem"],
        "solution": r["solution"],
        "audience": list(r["audience"] or []),
        "kpis": list(r["kpis"] or []),
        "effect": r["effect"],
        "cost_range": r["cost_range"],
        "budget_use": r["budget_use"],
        "timeline": r["timeline"],
        "tags": list(r["tags"] or []),
        "tag_labels": [tag_label(t) for t in (r["tags"] or [])],
        "status": r["status"],
        "decision": r["decision"],
        "review_text": r["review_text"],
        "reviewed_at": r["reviewed_at"].isoformat() if r["reviewed_at"] else None,
        "sla_deadline": r["sla_deadline"].isoformat() if r["sla_deadline"] else None,
    }


@router.post("/{review_id}", response_model=dict)
async def submit_review(
    review_id: str,
    data: ReviewSubmit,
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit an expert decision + written review."""
    if not _is_expert(user):
        raise HTTPException(status_code=403, detail="Experts only")

    row = await db.execute(
        text("SELECT id, project_id, reviewed_at FROM reviews WHERE id = :rid AND expert_id = :eid LIMIT 1"),
        {"rid": review_id, "eid": str(user.id)},
    )
    review = row.mappings().first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found or not assigned to you")
    if review["reviewed_at"]:
        raise HTTPException(status_code=400, detail="Already reviewed")

    await db.execute(
        text("""
            UPDATE reviews
            SET decision = :d, review_text = :t, reviewed_at = now()
            WHERE id = :rid
        """),
        {"d": data.decision, "t": data.review_text, "rid": review_id},
    )

    project_id = str(review["project_id"])
    final = await compute_and_apply_decision(db, project_id)

    # award XP to the expert for completing a review
    try:
        await db.execute(
            text("""
                INSERT INTO xp_transactions (user_id, amount, reason, icon)
                VALUES (:uid, 30, 'Retsenziya yakunlandi', '📝')
            """),
            {"uid": str(user.id)},
        )
        await db.execute(
            text("UPDATE profiles SET season_xp = COALESCE(season_xp,0)+30, global_xp = COALESCE(global_xp,0)+30 WHERE id = :uid"),
            {"uid": str(user.id)},
        )
    except Exception:
        pass

    return {"ok": True, "project_status": final}
