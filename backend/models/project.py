import enum
from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, DateTime, ForeignKey,
    Enum as SAEnum, func, Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEW = "review"           # На экспертизе
    REVISION = "revision"       # На доработке
    CROWDSOURCE = "crowdsource" # Краудсорсинг
    INCUBATION = "incubation"   # Инкубатор
    MINISTRY = "ministry"       # В Минздраве
    PILOT = "pilot"             # Пилот
    SCALED = "scaled"           # Масштабирован
    REJECTED = "rejected"       # Отклонён
    ARCHIVED = "archived"       # Архив


class TagGroup(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"


class ProjectTag(Base):
    __tablename__ = "project_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    tag: Mapped[str] = mapped_column(String(100))

    project = relationship("Project", back_populates="tags")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Step 1: Identification
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    elevator_pitch: Mapped[str | None] = mapped_column(Text)  # ≤150 words

    # Step 2: Problem & Solution
    problem: Mapped[str | None] = mapped_column(Text)   # ≤1500 chars
    solution: Mapped[str | None] = mapped_column(Text)  # ≤1500 chars
    audience: Mapped[str | None] = mapped_column(String(500))  # JSON array

    # Step 3: Results / KPI
    kpi: Mapped[str | None] = mapped_column(Text)  # JSON array of KPIs
    social_economic_effect: Mapped[str | None] = mapped_column(Text)

    # Step 4: Resources
    budget_min: Mapped[int | None] = mapped_column(Integer)
    budget_max: Mapped[int | None] = mapped_column(Integer)
    budget_purpose: Mapped[str | None] = mapped_column(Text)
    timeline: Mapped[str | None] = mapped_column(String(50))

    # Step 5: Documents
    documents: Mapped[str | None] = mapped_column(Text)  # JSON array of URLs

    # Status & workflow
    status: Mapped[ProjectStatus] = mapped_column(SAEnum(ProjectStatus), default=ProjectStatus.DRAFT)
    current_mentor_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    review_count: Mapped[int] = mapped_column(Integer, default=0)

    # Pilot data
    pilot_institution: Mapped[str | None] = mapped_column(String(255))
    pilot_started_at: Mapped[datetime | None] = mapped_column(DateTime)
    pilot_kpi_data: Mapped[str | None] = mapped_column(Text)  # JSON

    # Public stats
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    is_anonymous_in_review: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Relationships
    author = relationship("User", back_populates="projects", foreign_keys=[author_id])
    mentor = relationship("User", foreign_keys=[current_mentor_id])
    tags = relationship("ProjectTag", back_populates="project", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="project")
    comments = relationship("Comment", back_populates="project")
    mentorship = relationship("Mentorship", back_populates="project", uselist=False)
