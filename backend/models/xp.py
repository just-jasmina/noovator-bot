from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class XPTransaction(Base):
    __tablename__ = "xp_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(100))  # e.g. "project_approved"
    description: Mapped[str | None] = mapped_column(Text)
    reference_id: Mapped[int | None] = mapped_column(Integer)  # project_id or review_id
    is_seasonal: Mapped[bool] = mapped_column(Boolean, default=True)
    is_rolled_back: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="xp_transactions")


class XPRule(Base):
    __tablename__ = "xp_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    xp_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_per_day: Mapped[int | None] = mapped_column(Integer)
    max_total: Mapped[int | None] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))  # e.g. "Q1-2026"
    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[datetime] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    snapshot: Mapped[str | None] = mapped_column(Text)  # JSON snapshot of rankings
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
