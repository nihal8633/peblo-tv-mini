from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PublishRun(Base):
    __tablename__ = "publish_runs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    triggered_by: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    published_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    error_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )