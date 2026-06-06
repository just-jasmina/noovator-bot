from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..middleware.auth import get_active_user
from ..models.user import User, UserRole, UserLeague
from ..models.project import Project, ProjectStatus
from ..models.mentorship import Mentorship, MentorshipStatus, IncubatorMessage, Milestone

router = APIRouter(prefix="/mentorship", tags=["mentorship"])


@router.get("/exchange")
async def mentor_exchange(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_active_user),
):
    """List of free Innovators available as mentors."""
    result = await db.execute(
        select(User).where(User.league == UserLeague.INNOVATOR, User.status == "active")
    )
    innovators = result.scalars().all()

    output = []
    for inv in innovators:
        # Count active mentorships (max 2 slots)
        count_result = await db.execute(
            select(func.count(Mentorship.id)).where(
                and_(Mentorship.mentor_id == inv.id, Mentorship.status == MentorshipStatus.ACTIVE)
            )
        )
        active_count = count_result.scalar() or 0
        output.append({
            "user_id": inv.id,
            "first_name": inv.first_name,
            "last_name": inv.last_name,
            "avatar_url": inv.avatar_url,
            "tags": [t.strip() for t in (inv.expert_tags or "").split(",") if t.strip()],
            "global_xp": inv.global_xp,
            "active_mentorships": active_count,
            "slots_available": max(0, 2 - active_count),
        })

    return sorted(output, key=lambda x: x["slots_available"], reverse=True)


class MentorshipRequest(BaseModel):
    mentor_id: int
    project_id: int


@router.post("/request")
async def request_mentor(
    data: MentorshipRequest,
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate project
    proj_result = await db.execute(
        select(Project).where(and_(Project.id == data.project_id, Project.author_id == user.id))
    )
    project = proj_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.status != ProjectStatus.CROWDSOURCE:
        raise HTTPException(status_code=400, detail="Project must be in crowdsource stage")

    # Validate mentor
    mentor_result = await db.execute(
        select(User).where(and_(User.id == data.mentor_id, User.league == UserLeague.INNOVATOR))
    )
    mentor = mentor_result.scalar_one_or_none()
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found or not an Innovator")

    # Check mentor slots
    slot_count = await db.execute(
        select(func.count(Mentorship.id)).where(
            and_(Mentorship.mentor_id == mentor.id, Mentorship.status == MentorshipStatus.ACTIVE)
        )
    )
    if (slot_count.scalar() or 0) >= 2:
        raise HTTPException(status_code=400, detail="Mentor has no available slots")

    link = Mentorship(
        mentor_id=mentor.id,
        mentee_id=user.id,
        project_id=project.id,
        mentee_accepted=True,
    )
    db.add(link)
    await db.flush()
    return {"mentorship_id": link.id, "status": "pending_mentor_accept"}


@router.post("/{mentorship_id}/accept")
async def accept_mentorship(
    mentorship_id: int,
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Mentorship).where(Mentorship.id == mentorship_id)
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Mentorship not found")

    if user.id == link.mentor_id:
        link.mentor_accepted = True
    elif user.id == link.mentee_id:
        link.mentee_accepted = True
    else:
        raise HTTPException(status_code=403, detail="Not involved in this mentorship")

    if link.mentor_accepted and link.mentee_accepted:
        link.status = MentorshipStatus.ACTIVE
        project = link.project
        project.status = ProjectStatus.INCUBATION
        project.current_mentor_id = link.mentor_id

    await db.flush()
    return {"status": link.status}


@router.get("/{mentorship_id}/incubator")
async def get_incubator(
    mentorship_id: int,
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Mentorship).where(Mentorship.id == mentorship_id))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Not found")
    if user.id not in (link.mentor_id, link.mentee_id) and user.role not in (UserRole.ADMIN,):
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "status": link.status,
        "mentor_ready": link.mentor_ready,
        "messages": [
            {"id": m.id, "sender_id": m.sender_id, "content": m.content, "created_at": m.created_at}
            for m in link.messages
        ],
        "documents": [
            {"id": d.id, "title": d.title, "url": d.file_url, "type": d.doc_type}
            for d in link.documents
        ],
        "milestones": [
            {"id": ms.id, "title": ms.title, "is_done": ms.is_done, "due_date": ms.due_date}
            for ms in link.milestones
        ],
    }


class MessageCreate(BaseModel):
    content: str


@router.post("/{mentorship_id}/messages")
async def send_incubator_message(
    mentorship_id: int,
    data: MessageCreate,
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Mentorship).where(Mentorship.id == mentorship_id))
    link = result.scalar_one_or_none()
    if not link or user.id not in (link.mentor_id, link.mentee_id):
        raise HTTPException(status_code=403, detail="Access denied")

    msg = IncubatorMessage(mentorship_id=mentorship_id, sender_id=user.id, content=data.content)
    db.add(msg)
    link.last_mentor_activity = datetime.now(timezone.utc) if user.id == link.mentor_id else link.last_mentor_activity
    await db.flush()
    return {"id": msg.id, "content": msg.content, "created_at": msg.created_at}


@router.post("/{mentorship_id}/ready")
async def mark_ready_for_defense(
    mentorship_id: int,
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Mentorship).where(Mentorship.id == mentorship_id))
    link = result.scalar_one_or_none()
    if not link or user.id != link.mentor_id:
        raise HTTPException(status_code=403, detail="Only the mentor can mark as ready")

    link.mentor_ready = True
    link.project.status = ProjectStatus.MINISTRY
    await db.flush()
    return {"status": "sent_to_ministry"}
