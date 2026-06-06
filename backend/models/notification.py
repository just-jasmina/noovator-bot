import enum
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Boolean, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class NotificationType(str, enum.Enum):
    VERIFICATION_APPROVED = "verification_approved"
    VERIFICATION_REJECTED = "verification_rejected"
    REVIEW_VERDICT = "review_verdict"
    MENTOR_REQUEST = "mentor_request"
    MENTOR_ACCEPTED = "mentor_accepted"
    LEAGUE_PROMOTED = "league_promoted"
    LEAGUE_RELEGATED = "league_relegated"
    PROJECT_TO_PILOT = "project_to_pilot"
    PROJECT_SCALED = "project_scaled"
    SLA_WARNING = "sla_warning"
    COMMENT_REPLY = "comment_reply"
    XP_EARNED = "xp_earned"
    SYSTEM = "system"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    type: Mapped[NotificationType] = mapped_column(SAEnum(NotificationType))
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    deep_link: Mapped[str | None] = mapped_column(String(500))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_via_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="notifications")
