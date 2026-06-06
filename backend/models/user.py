import enum
from datetime import datetime
from sqlalchemy import (
    BigInteger, String, Integer, DateTime, Boolean,
    Enum as SAEnum, Text, Date, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class UserRole(str, enum.Enum):
    USER = "user"
    EXPERT = "expert"
    MENTOR = "mentor"
    MODERATOR = "moderator"
    ADMIN = "admin"


class UserLeague(str, enum.Enum):
    NOVICE = "novice"
    AMATEUR = "amateur"
    PROFESSIONAL = "professional"
    INNOVATOR = "innovator"


class UserStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REJECTED = "rejected"
    BANNED = "banned"


class UserGender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"


class UserAccountStatus(str, enum.Enum):
    STUDENT_SCHOOL = "school"
    STUDENT_BACHELOR = "bachelor"
    STUDENT_MASTER = "master"
    STUDENT_PHD = "phd"
    WORKER = "worker"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True, index=True)
    telegram_username: Mapped[str | None] = mapped_column(String(64))
    telegram_first_name: Mapped[str | None] = mapped_column(String(64))
    telegram_last_name: Mapped[str | None] = mapped_column(String(64))

    # Personal data
    pnfl: Mapped[str | None] = mapped_column(String(14), unique=True)
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    middle_name: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    birth_date: Mapped[datetime | None] = mapped_column(Date)
    gender: Mapped[UserGender | None] = mapped_column(SAEnum(UserGender))
    avatar_url: Mapped[str | None] = mapped_column(String(500))

    # Location
    region_type: Mapped[str | None] = mapped_column(String(20))  # uzbekistan / abroad
    region: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(Text)

    # Professional
    account_status: Mapped[UserAccountStatus | None] = mapped_column(SAEnum(UserAccountStatus))
    diploma_specialty: Mapped[str | None] = mapped_column(String(255))
    current_specialty: Mapped[str | None] = mapped_column(String(255))
    workplace: Mapped[str | None] = mapped_column(String(255))
    study_place: Mapped[str | None] = mapped_column(String(255))
    diploma_url: Mapped[str | None] = mapped_column(String(500))

    # Roles & gamification
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.USER)
    league: Mapped[UserLeague] = mapped_column(SAEnum(UserLeague), default=UserLeague.NOVICE)
    status: Mapped[UserStatus] = mapped_column(SAEnum(UserStatus), default=UserStatus.PENDING)
    season_xp: Mapped[int] = mapped_column(Integer, default=0)
    global_xp: Mapped[int] = mapped_column(Integer, default=0)
    expert_tags: Mapped[str | None] = mapped_column(String(500))  # comma-separated

    # Expert credentials (for web login, independent of Telegram)
    expert_username: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    expert_password_hash: Mapped[str | None] = mapped_column(String(255))

    # Notifications
    language: Mapped[str] = mapped_column(String(5), default="uz")
    last_active: Mapped[datetime | None] = mapped_column(DateTime)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_streak_date: Mapped[datetime | None] = mapped_column(Date)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    projects = relationship("Project", back_populates="author", foreign_keys="Project.author_id")
    reviews = relationship("Review", back_populates="expert")
    comments = relationship("Comment", back_populates="author")
    xp_transactions = relationship("XPTransaction", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    mentor_links = relationship("Mentorship", back_populates="mentor", foreign_keys="Mentorship.mentor_id")
    mentee_links = relationship("Mentorship", back_populates="mentee", foreign_keys="Mentorship.mentee_id")
