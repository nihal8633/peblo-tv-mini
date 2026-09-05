from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Show
from app.security import require_editor
from app.services.publish import VALID_SECTIONS


router = APIRouter(prefix="/shows", tags=["Shows"])


ALLOWED_STATUSES = {"draft", "published"}


class ShowCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=255)
    synopsis: str = Field(min_length=1)
    section: str | None = Field(default=None, max_length=50)


class ShowUpdate(BaseModel):
    slug: str | None = Field(default=None, min_length=1, max_length=200)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    synopsis: str | None = Field(default=None, min_length=1)
    section: str | None = Field(default=None, max_length=50)
    status: str | None = None


def validate_show_fields(section: str | None, status: str):
    if status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid status '{status}'. "
                f"Allowed statuses: {', '.join(sorted(ALLOWED_STATUSES))}"
            ),
        )

    if section is not None and section not in VALID_SECTIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid section '{section}'. "
                f"Allowed sections: {', '.join(sorted(VALID_SECTIONS))}"
            ),
        )


@router.get("")
def list_shows(
    q: str | None = Query(default=None, min_length=1),
    section: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    query = select(Show)

    if q:
        search = f"%{q.strip()}%"
        query = query.where(
            or_(
                Show.title.ilike(search),
                Show.slug.ilike(search),
                Show.synopsis.ilike(search),
            )
        )

    if section:
        if section not in VALID_SECTIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid section '{section}'. "
                    f"Allowed sections: {', '.join(sorted(VALID_SECTIONS))}"
                ),
            )

        query = query.where(Show.section == section)

    if status:
        if status not in ALLOWED_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid status '{status}'. "
                    f"Allowed statuses: {', '.join(sorted(ALLOWED_STATUSES))}"
                ),
            )

        query = query.where(Show.status == status)

    query = query.order_by(
        Show.title,
        Show.id,
    )

    shows = db.scalars(
        query.offset((page - 1) * page_size).limit(page_size)
    ).all()

    return {
        "items": [
            {
                "id": show.id,
                "slug": show.slug,
                "title": show.title,
                "synopsis": show.synopsis,
                "section": show.section,
                "status": show.status,
            }
            for show in shows
        ],
        "page": page,
        "page_size": page_size,
        "count": len(shows),
    }


@router.get("/{show_id}")
def get_show(
    show_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    show = db.get(Show, show_id)

    if not show:
        raise HTTPException(
            status_code=404,
            detail="Show not found.",
        )

    return {
        "id": show.id,
        "slug": show.slug,
        "title": show.title,
        "synopsis": show.synopsis,
        "section": show.section,
        "status": show.status,
        "seasons": [
            {
                "id": season.id,
                "season_number": season.season_number,
            }
            for season in sorted(
                show.seasons,
                key=lambda season: season.season_number,
            )
        ],
    }


@router.post("")
def create_show(
    payload: ShowCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    validate_show_fields(
        section=payload.section,
        status="draft",
    )

    existing_show = db.scalar(
        select(Show).where(Show.slug == payload.slug)
    )

    if existing_show:
        raise HTTPException(
            status_code=409,
            detail="A show with this slug already exists.",
        )

    show = Show(
        slug=payload.slug,
        title=payload.title,
        synopsis=payload.synopsis,
        section=payload.section,
        status="draft",
    )

    db.add(show)

    try:
        db.commit()
        db.refresh(show)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Show could not be created because the slug already exists.",
        ) from exc

    return {
        "id": show.id,
        "slug": show.slug,
        "title": show.title,
        "synopsis": show.synopsis,
        "section": show.section,
        "status": show.status,
    }


@router.patch("/{show_id}")
def update_show(
    show_id: int,
    payload: ShowUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    show = db.get(Show, show_id)

    if not show:
        raise HTTPException(
            status_code=404,
            detail="Show not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    if show.status == "published":
        raise HTTPException(
            status_code=409,
            detail=(
                "Published shows cannot be edited directly. "
                "Create a new draft version instead."
            ),
        )

    requested_status = update_data.get(
        "status",
        show.status,
    )

    requested_section = update_data.get(
        "section",
        show.section,
    )

    validate_show_fields(
        section=requested_section,
        status=requested_status,
    )

    if requested_status == "published" and not requested_section:
        raise HTTPException(
            status_code=400,
            detail="A section is required before publishing a show.",
        )

    new_slug = update_data.get(
        "slug",
        show.slug,
    )

    duplicate_slug = db.scalar(
        select(Show).where(
            Show.slug == new_slug,
            Show.id != show.id,
        )
    )

    if duplicate_slug:
        raise HTTPException(
            status_code=409,
            detail="A show with this slug already exists.",
        )

    for field, value in update_data.items():
        if field == "status":
            continue

        setattr(show, field, value)

    show.status = requested_status

    try:
        db.commit()
        db.refresh(show)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Show could not be updated because the slug already exists.",
        ) from exc

    return {
        "id": show.id,
        "slug": show.slug,
        "title": show.title,
        "synopsis": show.synopsis,
        "section": show.section,
        "status": show.status,
    }