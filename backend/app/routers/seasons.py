from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Season, Show
from app.security import require_editor


router = APIRouter(
    prefix="/seasons",
    tags=["Seasons"],
)


class SeasonCreate(BaseModel):
    show_id: int
    season_number: int = Field(ge=1)


class SeasonUpdate(BaseModel):
    season_number: int = Field(ge=1)


def season_response(season: Season):
    return {
        "id": season.id,
        "show_id": season.show_id,
        "season_number": season.season_number,
    }


@router.get("/show/{show_id}")
def list_seasons(
    show_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    show = db.get(Show, show_id)

    if show is None:
        raise HTTPException(
            status_code=404,
            detail="Show not found",
        )

    seasons = db.scalars(
        select(Season)
        .where(Season.show_id == show_id)
        .order_by(Season.season_number, Season.id)
    ).all()

    return [
        season_response(season)
        for season in seasons
    ]


@router.get("/{season_id}")
def get_season(
    season_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    season = db.get(Season, season_id)

    if season is None:
        raise HTTPException(
            status_code=404,
            detail="Season not found",
        )

    return season_response(season)


@router.post("", status_code=201)
def create_season(
    data: SeasonCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    show = db.get(Show, data.show_id)

    if show is None:
        raise HTTPException(
            status_code=404,
            detail="Show not found",
        )

    if show.status == "published":
        raise HTTPException(
            status_code=409,
            detail="Published shows cannot have seasons added directly.",
        )

    if data.season_number == 0:
        raise HTTPException(
            status_code=400,
            detail="Season 0 is reserved for trailers.",
        )

    existing = db.scalar(
        select(Season).where(
            Season.show_id == data.show_id,
            Season.season_number == data.season_number,
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="That season already exists for this show.",
        )

    season = Season(
        show_id=data.show_id,
        season_number=data.season_number,
    )

    db.add(season)

    try:
        db.commit()
        db.refresh(season)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="That season already exists for this show.",
        ) from exc

    return season_response(season)


@router.patch("/{season_id}")
def update_season(
    season_id: int,
    data: SeasonUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    season = db.get(Season, season_id)

    if season is None:
        raise HTTPException(
            status_code=404,
            detail="Season not found",
        )

    show = db.get(Show, season.show_id)

    if show is not None and show.status == "published":
        raise HTTPException(
            status_code=409,
            detail="Published shows cannot have seasons edited directly.",
        )

    if data.season_number == 0:
        raise HTTPException(
            status_code=400,
            detail="Season 0 is reserved for trailers.",
        )

    existing = db.scalar(
        select(Season).where(
            Season.show_id == season.show_id,
            Season.season_number == data.season_number,
            Season.id != season.id,
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="That season already exists for this show.",
        )

    season.season_number = data.season_number

    try:
        db.commit()
        db.refresh(season)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="That season already exists for this show.",
        ) from exc

    return season_response(season)


@router.delete("/{season_id}")
def delete_season(
    season_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    season = db.get(Season, season_id)

    if season is None:
        raise HTTPException(
            status_code=404,
            detail="Season not found",
        )

    show = db.get(Show, season.show_id)

    if show is not None and show.status == "published":
        raise HTTPException(
            status_code=409,
            detail="Published shows cannot have seasons deleted directly.",
        )

    if season.episodes:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a season that still contains episodes.",
        )

    db.delete(season)
    db.commit()

    return {
        "message": "Season deleted successfully",
        "season_id": season_id,
    }