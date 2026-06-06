import enum
from datetime import datetime
from sqlalchemy import Integer, Text, DateTime, ForeignKey, Enum as SAEnum, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class ReviewDecision(str, enum.Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REVISION = "revision"


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    expert_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    decision: Mapped[ReviewDecision | None] = mapped_column(SAEnum(ReviewDecision))
    review_text: Mapped[str | None] = mapped_column(Text)  # min 150 words
    checklist: Mapped[str | None] = mapped_column(Text)    # JSON, used for revision

    is_backup: Mapped[bool] = mapped_column(Boolean, default=False)
    sla_deadline: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    is_overdue: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    project = relationship("Project", back_populates="reviews")
    expert = relationship("User", back_populates="reviews")
