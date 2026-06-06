from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from pydantic import BaseModel
from ..database import get_db
from ..middleware.auth import get_active_user
from ..models.user import User, UserRole
from ..models.project import Project, ProjectStatus
from ..models.comment import Comment
from ..services.xp_engine import award_xp

router = APIRouter(prefix="/comments", tags=["comments"])


class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None


@router.get("/project/{project_id}", response_model=List[dict])
async def get_comments(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Comment).where(
            and_(Comment.project_id == project_id, Comment.is_hidden == False, Comment.parent_id == None)
        )
    )
    comments = result.scalars().all()
    output = []
    for c in comments:
        replies_result = await db.execute(
            select(Comment).where(
                and_(Comment.parent_id == c.id, Comment.is_hidden == False)
            )
        )
        replies = replies_result.scalars().all()
        author = c.author
        output.append({
            "id": c.id,
            "content": c.content,
            "author_id": c.author_id,
            "author_name": f"{author.first_name or ''} {author.last_name or ''}".strip() if author else "Anonymous",
            "author_league": author.league if author else None,
            "author_avatar": author.avatar_url if author else None,
            "created_at": c.created_at,
            "replies": [
                {
                    "id": r.id,
                    "content": r.content,
                    "author_id": r.author_id,
                    "author_name": f"{r.author.first_name or ''} {r.author.last_name or ''}".strip() if r.author else "Anonymous",
                    "created_at": r.created_at,
                }
                for r in replies
            ],
        })
    return output


@router.post("/project/{project_id}", response_model=dict, status_code=201)
async def add_comment(
    project_id: int,
    data: CommentCreate,
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.status not in (ProjectStatus.CROWDSOURCE, ProjectStatus.MINISTRY, ProjectStatus.PILOT, ProjectStatus.SCALED):
        raise HTTPException(status_code=400, detail="Comments not allowed in this stage")

    comment = Comment(
        project_id=project_id,
        author_id=user.id,
        content=data.content,
        parent_id=data.parent_id,
    )
    db.add(comment)
    project.comment_count += 1

    # Award XP if 50+ chars
    if len(data.content) >= 50 and not comment.xp_awarded:
        await award_xp(db, user, "comment_constructive", f"Comment on project #{project_id}", project_id)
        comment.xp_awarded = True

    await db.flush()
    return {"id": comment.id, "content": comment.content, "created_at": comment.created_at}


@router.delete("/{comment_id}")
async def hide_comment(
    comment_id: int,
    user: User = Depends(get_active_user),
    db: AsyncSession = Depends(get_db),
):
    from ..models.user import UserLeague
    if user.role not in (UserRole.ADMIN, UserRole.MODERATOR) and user.league != UserLeague.PROFESSIONAL:
        raise HTTPException(status_code=403, detail="Professionals and above can hide comments")

    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment.is_hidden = True
    await db.flush()
    return {"status": "hidden"}
