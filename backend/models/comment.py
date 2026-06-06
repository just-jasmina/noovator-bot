from datetime import datetime
from sqlalchemy import Integer, Text, DateTime, ForeignKey, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("comments.id"))

    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    xp_awarded: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="comments")
    author = relationship("User", back_populates="comments")
    parent = relationship("Comment", remote_side="Comment.id", backref="replies")
