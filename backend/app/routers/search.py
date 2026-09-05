from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Episode, Season, Show


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


ALLOWED_SECTIONS = {
    "featured",
    "series",
    "minisodes",
    "songs",
}

ALLOWED_LANGUAGES = {
    "en",
    "hi",
}

ALLOWED_CATEGORIES = {
    "adventure",
    "folk",
    "friendship",
    "india",
    "language",
    "learning",
    "maths",
    "music",
    "nature",
    "reading",
    "science",
    "singalong",
    "stories",
    "travel",
    "values",
}


@router.get("")
def search_catalogue(
    q: str | None = None,
    category: str | None = None,
    language: str | None = None,
    section: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    if category is not None and category not in ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category '{category}'.",
        )

    if language is not None and language not in ALLOWED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid language '{language}'.",
        )

    if section is not None and section not in ALLOWED_SECTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid section '{section}'.",
        )

    query = (
        select(Episode, Show)
        .join(
            Season,
            Episode.season_id == Season.id,
        )
        .join(
            Show,
            Season.show_id == Show.id,
        )
        .where(
            Show.status == "published",
            Episode.status == "published",
            Season.season_number != 0,
        )
    )

    if q and q.strip():
        search_text = q.strip()
        search_term = f"%{search_text}%"

        query = query.where(
            or_(
                Show.title.ilike(search_term),
                Episode.title.ilike(search_term),
                Episode.categories.any(search_text),
            )
        )

    if category:
        query = query.where(
            Episode.categories.any(category)
        )

    if language:
        query = query.where(
            Episode.language == language
        )

    if section:
        query = query.where(
            Show.section == section
        )

    query = query.order_by(
        Show.title,
        Season.season_number,
        Episode.episode_number,
        Episode.id,
    )

    offset = (page - 1) * page_size

    results = db.execute(
        query.offset(offset).limit(page_size)
    ).all()

    return {
        "page": page,
        "page_size": page_size,
        "count": len(results),
        "results": [
            {
                "show": {
                    "slug": show.slug,
                    "title": show.title,
                    "section": show.section,
                },
                "episode": {
                    "episode_id": episode.episode_id,
                    "title": episode.title,
                    "episode_number": episode.episode_number,
                    "duration_seconds": episode.duration_seconds,
                    "language": episode.language,
                    "content_group": episode.content_group,
                    "categories": episode.categories or [],
                },
            }
            for episode, show in results
        ],
    }