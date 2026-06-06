"""Supabase-native project endpoints (UUID schema, raw SQL)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

from ..database import get_db
from ..middleware.auth import get_active_user
from ..models.user import User
from ..services.tag_routing import normalize_tags, tag_label, assign_experts_supabase

router = APIRouter(prefix="/projects", tags=["projects"])

# Statuses visible in the public feed
PUBLIC_STATUSES = ("crowdsource", "approved", "pilot", "scaled", "ministry", "incubation")


class ProjectCreateReq(BaseModel):
    title: str
    elevator_pitch: Optional[str] = ""
    tags: List[str] = []
    problem: Optional[str] = ""
    solution: Optional[str] = ""
    audience: Optional[List[str]] = []
    kpi: Optional[list] = []
    social_economic_effect: Optional[str] = ""
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    budget_purpose: Optional[str] = ""
    timeline: Optional[str] = ""


def _kpis_to_text(kpi) -> list[str]:
    """Frontend sends [{label,value}]; store as 'label: value' strings."""
    out = []
    for k in kpi or []:
        if isinstance(k, dict):
            label = (k.get("label") or "").strip()
            value = (k.get("value") or "").strip()
            if label:
                out.append(f"{label}: {value}" if value else label)
        elif isinstance(k, str) and k.strip():
            out.append(k.strip())
    return out


def _serialize(r: dict) -> dict:
    tags = list(r.get("tags") or [])
    return {
        "id": str(r["id"]),
        "title": r["title"],
        "elevator_pitch": r.get("pitch"),
        "pitch": r.get("pitch"),
        "tags": tags,
        "tag_labels": [tag_label(t) for t in tags],
        "status": r.get("status"),
        "author_id": str(r["user_id"]) if r.get("user_id") else None,
        "author_name": r.get("author_name"),
        "comment_count": r.get("comments_count") or 0,
        "view_count": r.get("likes_count") or 0,
        "likes_count": r.get("likes_count") or 0,
        "has_mentor": False,
        "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
    }


@router.get("", response_model=List[dict])
async def list_projects(
    tag: Optional[str] = Query(None),
    sort: str = Query("newest", regex="^(newest|popular|discussed)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    order = {
        "popular": "pr.likes_count DESC",
        "discussed": "pr.comments_count DESC",
    }.get(sort, "pr.created_at DESC")

    params = {"statuses": list(PUBLIC_STATUSES), "lim": size, "off": (page - 1) * size}
    tag_filter = ""
    if tag:
        params["tag"] = normalize_tags([tag])
        tag_filter = "AND pr.tags && CAST(:tag AS text[])"

    rows = await db.execute(
        text(f"""
            SELECT pr.*,
                   (SELECT full_name FROM profiles a WHERE a.id = pr.user_id) AS author_name
            FROM projects pr
            WHERE pr.status = ANY(:statuses) {tag_filter}
            ORDER BY {order}
            LIMIT :lim OFFSET :off
        """),
        params,
    )
    return [_serialize(dict(r)) for r in rows.mappings().all()]


@router.post("", response_model=dict, status_code=201)
async def create_project(
    data: ProjectCreateReq,
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    tags = normalize_tags(data.tags)
    if not tags:
        raise HTTPException(status_code=400, detail="Kamida 1 ta teg tanlang")

    budget_parts = []
    if data.budget_min is not None:
        budget_parts.append(str(data.budget_min))
    if data.budget_max is not None:
        budget_parts.append(str(data.budget_max))
    cost_range = " - ".join(budget_parts)

    row = await db.execute(
        text("""
            INSERT INTO projects
                (user_id, title, pitch, tags, problem, solution, audience, kpis,
                 effect, cost_range, budget_use, timeline, status)
            VALUES
                (:uid, :title, :pitch, CAST(:tags AS text[]), :problem, :solution,
                 CAST(:audience AS text[]), CAST(:kpis AS text[]),
                 :effect, :cost_range, :budget_use, :timeline, 'under_review')
            RETURNING *
        """),
        {
            "uid": str(user.id),
            "title": data.title,
            "pitch": data.elevator_pitch or "",
            "tags": tags,
            "problem": data.problem or "",
            "solution": data.solution or "",
            "audience": list(data.audience or []),
            "kpis": _kpis_to_text(data.kpi),
            "effect": data.social_economic_effect or "",
            "cost_range": cost_range,
            "budget_use": data.budget_purpose or "",
            "timeline": data.timeline or "",
        },
    )
    project = dict(row.mappings().first())
    project_id = str(project["id"])

    # Route to experts by tag
    assigned = await assign_experts_supabase(db, project_id, tags)

    # Award XP to the author
    try:
        await db.execute(
            text("INSERT INTO xp_transactions (user_id, amount, reason, icon) VALUES (:uid, 50, 'Loyiha yuborildi', '🚀')"),
            {"uid": str(user.id)},
        )
        await db.execute(
            text("UPDATE profiles SET season_xp = COALESCE(season_xp,0)+50, global_xp = COALESCE(global_xp,0)+50 WHERE id = :uid"),
            {"uid": str(user.id)},
        )
    except Exception:
        pass

    result = _serialize(project)
    result["assigned_experts"] = len(assigned)
    return result


@router.get("/my", response_model=List[dict])
async def my_projects(
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(
        text("SELECT * FROM projects WHERE user_id = :uid ORDER BY created_at DESC"),
        {"uid": str(user.id)},
    )
    return [_serialize(dict(r)) for r in rows.mappings().all()]


@router.get("/{project_id}", response_model=dict)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    row = await db.execute(
        text("""
            SELECT pr.*,
                   (SELECT full_name FROM profiles a WHERE a.id = pr.user_id) AS author_name
            FROM projects pr WHERE pr.id = :pid LIMIT 1
        """),
        {"pid": project_id},
    )
    r = row.mappings().first()
    if not r:
        raise HTTPException(status_code=404, detail="Project not found")

    detail = _serialize(dict(r))
    detail.update({
        "problem": r["problem"],
        "solution": r["solution"],
        "audience": list(r["audience"] or []),
        "kpi": list(r["kpis"] or []),
        "social_economic_effect": r["effect"],
        "budget_purpose": r["budget_use"],
        "cost_range": r["cost_range"],
        "timeline": r["timeline"],
    })
    return detail
