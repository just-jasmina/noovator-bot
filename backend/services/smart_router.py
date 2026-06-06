from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta, timezone
from ..models.user import User, UserRole
from ..models.project import Project
from ..models.review import Review, ReviewDecision


async def assign_experts(db: AsyncSession, project: Project) -> list[User]:
    """
    Smart routing: assign 3 experts matching project tags with lowest load.
    Returns list of assigned expert Users.
    """
    project_tags = {t.tag for t in project.tags}

    # Get all active experts
    result = await db.execute(
        select(User).where(
            and_(User.role == UserRole.EXPERT, User.status == "active")
        )
    )
    experts = result.scalars().all()

    # Filter by matching tags and sort by load (fewest active reviews)
    scored = []
    for expert in experts:
        expert_tag_set = set(
            t.strip() for t in (expert.expert_tags or "").split(",") if t.strip()
        )
        overlap = len(project_tags & expert_tag_set)
        if overlap == 0:
            continue

        # Count active (incomplete) reviews for load balancing
        load_result = await db.execute(
            select(func.count(Review.id)).where(
                and_(
                    Review.expert_id == expert.id,
                    Review.completed_at == None,
                )
            )
        )
        load = load_result.scalar() or 0
        scored.append((expert, overlap, load))

    # Sort: max tag overlap first, then min load
    scored.sort(key=lambda x: (-x[1], x[2]))
    selected = [e for e, _, _ in scored[:3]]

    if len(selected) < 3:
        # Fill with any active experts not already selected
        existing_ids = {e.id for e in selected}
        fillers = [e for e in experts if e.id not in existing_ids]
        selected.extend(fillers[:3 - len(selected)])

    # Create Review assignments with SLA deadline (7 days)
    sla_deadline = datetime.now(timezone.utc) + timedelta(days=7)
    for expert in selected:
        review = Review(
            project_id=project.id,
            expert_id=expert.id,
            sla_deadline=sla_deadline,
        )
        db.add(review)

    await db.flush()
    return selected


async def compute_majority_decision(db: AsyncSession, project_id: int) -> str | None:
    """
    After all 3 experts vote, compute majority decision.
    Returns: 'approve' | 'reject' | 'revision' | None (not ready)
    """
    result = await db.execute(
        select(Review).where(
            and_(
                Review.project_id == project_id,
                Review.completed_at != None,
                Review.decision != None,
            )
        )
    )
    reviews = result.scalars().all()

    if len(reviews) < 2:
        return None

    counts = {ReviewDecision.APPROVE: 0, ReviewDecision.REJECT: 0, ReviewDecision.REVISION: 0}
    for r in reviews:
        counts[r.decision] += 1

    if counts[ReviewDecision.APPROVE] >= 2:
        return "approve"
    if counts[ReviewDecision.REJECT] >= 2:
        return "reject"
    if len(reviews) == 3:
        return "revision"
    return None
