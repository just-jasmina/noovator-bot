import enum
from datetime import datetime
from sqlalchemy import Integer, Text, DateTime, ForeignKey, Enum as SAEnum, func, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class MentorshipStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Mentorship(Base):
    __tablename__ = "mentorships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mentor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    mentee_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), unique=True)

    status: Mapped[MentorshipStatus] = mapped_column(SAEnum(MentorshipStatus), default=MentorshipStatus.PENDING)
    mentor_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    mentee_accepted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Anti-fraud
    last_mentor_activity: Mapped[datetime | None] = mapped_column(DateTime)
    mentor_ready: Mapped[bool] = mapped_column(Boolean, default=False)  # «Готов к защите»

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    mentor = relationship("User", back_populates="mentor_links", foreign_keys=[mentor_id])
    mentee = relationship("User", back_populates="mentee_links", foreign_keys=[mentee_id])
    project = relationship("Project", back_populates="mentorship")
    messages = relationship("IncubatorMessage", back_populates="mentorship", cascade="all, delete-orphan")
    documents = relationship("IncubatorDocument", back_populates="mentorship", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="mentorship", cascade="all, delete-orphan")


class IncubatorMessage(Base):
    __tablename__ = "incubator_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mentorship_id: Mapped[int] = mapped_column(Integer, ForeignKey("mentorships.id", ondelete="CASCADE"))
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    mentorship = relationship("Mentorship", back_populates="messages")
    sender = relationship("User")


class IncubatorDocument(Base):
    __tablename__ = "incubator_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mentorship_id: Mapped[int] = mapped_column(Integer, ForeignKey("mentorships.id", ondelete="CASCADE"))
    uploader_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    file_url: Mapped[str] = mapped_column(String(500))
    doc_type: Mapped[str | None] = mapped_column(String(50))  # budget/tz/presentation
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    mentorship = relationship("Mentorship", back_populates="documents")
    uploader = relationship("User")


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mentorship_id: Mapped[int] = mapped_column(Integer, ForeignKey("mentorships.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    mentorship = relationship("Mentorship", back_populates="milestones")
