from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from ..models.project import ProjectStatus


class ProjectCreate(BaseModel):
    title: str
    elevator_pitch: Optional[str] = None
    tags: List[str]
    problem: Optional[str] = None
    solution: Optional[str] = None
    audience: Optional[List[str]] = None
    kpi: Optional[List[dict]] = None
    social_economic_effect: Optional[str] = None
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    budget_purpose: Optional[str] = None
    timeline: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if len(v) > 100:
            raise ValueError("Title must be ≤100 characters")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        if not 1 <= len(v) <= 3:
            raise ValueError("Must have 1–3 tags")
        return v


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    elevator_pitch: Optional[str] = None
    tags: Optional[List[str]] = None
    problem: Optional[str] = None
    solution: Optional[str] = None
    audience: Optional[List[str]] = None
    kpi: Optional[List[dict]] = None
    social_economic_effect: Optional[str] = None
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    budget_purpose: Optional[str] = None
    timeline: Optional[str] = None


class TagOut(BaseModel):
    tag: str

    class Config:
        from_attributes = True


class ProjectCard(BaseModel):
    id: int
    title: str
    elevator_pitch: Optional[str] = None
    tags: List[str]
    status: ProjectStatus
    author_id: int
    author_name: Optional[str] = None
    author_league: Optional[str] = None
    comment_count: int
    view_count: int
    has_mentor: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectDetail(ProjectCard):
    problem: Optional[str] = None
    solution: Optional[str] = None
    audience: Optional[List[str]] = None
    kpi: Optional[List[dict]] = None
    social_economic_effect: Optional[str] = None
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    budget_purpose: Optional[str] = None
    timeline: Optional[str] = None
    documents: Optional[List[str]] = None
    expert_reviews: Optional[List[dict]] = None  # anonymous positive reviews
    updated_at: datetime
    submitted_at: Optional[datetime] = None
