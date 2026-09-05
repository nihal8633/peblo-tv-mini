from datetime import datetime

from sqlalchemy import (
    ARRAY,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Show(Base):
    __tablename__ = "shows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    slug: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    synopsis: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    section: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    seasons: Mapped[list["Season"]] = relationship(
        back_populates="show",
        cascade="all, delete-orphan",
    )


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    show_id: Mapped[int] = mapped_column(
        ForeignKey(
            "shows.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    season_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    show: Mapped["Show"] = relationship(
        back_populates="seasons",
    )

    episodes: Mapped[list["Episode"]] = relationship(
        back_populates="season",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "show_id",
            "season_number",
            name="uq_show_season",
        ),
    )


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    episode_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    season_id: Mapped[int] = mapped_column(
        ForeignKey(
            "seasons.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    episode_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    content_group: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
    )

    categories: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
    )

    season: Mapped["Season"] = relationship(
        back_populates="episodes",
    )

    artworks: Mapped[list["Artwork"]] = relationship(
        back_populates="episode",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "content_group",
            "language",
            name="uq_content_group_language",
        ),
    )


class Artwork(Base):
    __tablename__ = "artworks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    episode_id: Mapped[int] = mapped_column(
        ForeignKey(
            "episodes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    slot: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    object_key: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    width: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    height: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    episode: Mapped["Episode"] = relationship(
        back_populates="artworks",
    )

    __table_args__ = (
        UniqueConstraint(
            "episode_id",
            "slot",
            name="uq_episode_artwork_slot",
        ),
    )