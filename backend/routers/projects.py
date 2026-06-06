import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from typing import List, Optional
from ..database import get_db
from ..middleware.auth import get_active_user
from ..models.user import User, UserLeague
from ..models.project import Project, ProjectStatus, ProjectTag
from ..schemas.project import ProjectCreate, ProjectUpdate, ProjectCard, ProjectDetail
from ..services.xp_engine import award_xp
from ..services.smart_router import assign_experts
from ..services.notifications import notify_user
from ..models.notification import NotificationType

router = APIRouter(prefix="/projects", tags=["projects"])

LEAGUE_MAX_PROJECTS = {
    UserLeague.NOVICE: 1,
    UserLeague.AMATEUR: 3,
    UserLeague.PROFESSIONAL: 9999,
    UserLeague.INNOVATOR: 9999,
}


def _serialize_project(p: Project, user: User | None = None) -> dict:
    tags = [t.tag for t in p.tags]
    author = p.author
    return {
        "id": p.id,
        "title": p.title,
        "elevator_pitch": p.elevator_pitch,
        "tags": tags,
        "status": p.status,
        "author_id": p.author_id,
        "author_name": f"{author.first_name or ''} {author.last_name or ''}".strip() if author else None,
        "author_league": author.league if author else None,
        "comment_count": p.comment_count,
        "view_count": p.view_count,
        "has_mentor": p.mentorship is not None and p.mentorship.status == "active",
        "created_at": p.created_at,
    }


@router.get("", response_model=List[dict])
async def list_projects(
    tag: Optional[str] = Query(None),
    sort: str = Query("newest", regex="^(newest|popular|discussed)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Public project feed — only CROWDSOURCE and above statuses."""
    query = select(Project).where(
        Project.status.in_([
            ProjectStatus.CROWDSOURCE, ProjectStatus.INCUBATION,
            ProjectStatus.MINISTRY, ProjectStatus.PILOT, ProjectStatus.SCALED,
        ])
    )
    if tag:
        query = query.join(ProjectTag).where(ProjectTag.tag == tag)

    if sort == "popular":
        query = query.order_by(desc(Project.view_count))
    elif sort == "discussed":
        query = query.order_by(desc(Project.comment_count))
    else:
        query = query.order_by(desc(Project.created_at))

    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    result = await db.execute(query)
    projects = result.scalars().all()
    return [_serialize_project(p) for p in projects]


@router.post("", response_model=dict, status_code=201)
async def create_project(
    data: ProjectCreate,
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Check active projects limit per league
    max_active = LEAGUE_MAX_PROJECTS[user.league]
    active_count_result = await db.execute(
        select(func.count(Project.id)).where(
            and_(
                Project.author_id == user.id,
                Project.status.in_([ProjectStatus.REVIEW, ProjectStatus.REVISION]),
            )
        )
    )
    if active_count_result.scalar() >= max_active:
        raise HTTPException(
            status_code=400,
            detail=f"League limit reached: max {max_active} active project(s) in review"
        )

    project = Project(
        author_id=user.id,
        title=data.title,
        elevator_pitch=data.elevator_pitch,
        problem=data.problem,
        solution=data.solution,
        audience=json.dumps(data.audience or []),
        kpi=json.dumps(data.kpi or []),
        social_economic_effect=data.social_economic_effect,
        budget_min=data.budget_min,
        budget_max=data.budget_max,
        budget_purpose=data.budget_purpose,
        timeline=data.timeline,
        status=ProjectStatus.REVIEW,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(project)
    await db.flush()

    for tag_name in data.tags:
        db.add(ProjectTag(project_id=project.id, tag=tag_name))

    await assign_experts(db, project)
    await award_xp(db, user, "project_submitted", f"Submitted project #{project.id}", project.id)
    await db.flush()
    return _serialize_project(project)


@router.get("/my", response_model=List[dict])
async def my_projects(
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(Project.author_id == user.id).order_by(desc(Project.created_at))
    )
    return [_serialize_project(p, user) for p in result.scalars().all()]


@router.get("/{project_id}", response_model=dict)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Increment view count
    project.view_count += 1
    await db.flush()

    detail = _serialize_project(project)
    detail.update({
        "problem": project.problem,
        "solution": project.solution,
        "audience": json.loads(project.audience or "[]"),
        "kpi": json.loads(project.kpi or "[]"),
        "social_economic_effect": project.social_economic_effect,
        "budget_min": project.budget_min,
        "budget_max": project.budget_max,
        "budget_purpose": project.budget_purpose,
        "timeline": project.timeline,
        "documents": json.loads(project.documents or "[]"),
        "updated_at": project.updated_at,
        "submitted_at": project.submitted_at,
    })
    return detail


@router.put("/{project_id}", response_model=dict)
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project or project.author_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.status not in (ProjectStatus.DRAFT, ProjectStatus.REVISION):
        raise HTTPException(status_code=400, detail="Cannot edit project in this status")

    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "tags":
            # Replace tags
            for old_tag in project.tags:
                await db.delete(old_tag)
            for tag_name in value:
                db.add(ProjectTag(project_id=project.id, tag=tag_name))
        elif field in ("audience", "kpi"):
            setattr(project, field, json.dumps(value))
        else:
            setattr(project, field, value)

    await db.flush()
    return _serialize_project(project)


@router.post("/{project_id}/documents")
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project or project.author_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    max_size = 10 * 1024 * 1024
    if file.size and file.size > max_size:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    # In production: upload to S3
    file_url = f"/media/projects/{project_id}/{file.filename}"
    docs = json.loads(project.documents or "[]")
    docs.append({"name": file.filename, "url": file_url})
    project.documents = json.dumps(docs)
    await db.flush()
    return {"url": file_url}
