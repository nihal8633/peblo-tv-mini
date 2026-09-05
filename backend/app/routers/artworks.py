from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Artwork, Episode
from app.security import require_editor
from app.services.storage.local import LocalStorage
from app.services.validation import validate_artwork


router = APIRouter(
    prefix="/artworks",
    tags=["Artwork"],
)

storage = LocalStorage()


def artwork_response(artwork: Artwork):
    return {
        "id": artwork.id,
        "episode_id": artwork.episode_id,
        "slot": artwork.slot,
        "object_key": artwork.object_key,
        "width": artwork.width,
        "height": artwork.height,
        "size_bytes": artwork.size_bytes,
        "content_type": artwork.content_type,
    }


@router.get("/episode/{episode_id}")
def get_episode_artworks(
    episode_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    episode = db.get(Episode, episode_id)

    if episode is None:
        raise HTTPException(
            status_code=404,
            detail="Episode not found.",
        )

    artworks = (
        db.query(Artwork)
        .filter(Artwork.episode_id == episode_id)
        .order_by(Artwork.slot)
        .all()
    )

    return [
        artwork_response(artwork)
        for artwork in artworks
    ]


@router.post("/upload")
async def upload_artwork(
    episode_id: int = Form(...),
    slot: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    episode = db.get(Episode, episode_id)

    if episode is None:
        raise HTTPException(
            status_code=404,
            detail="Episode not found.",
        )

    if episode.status == "published":
        raise HTTPException(
            status_code=409,
            detail="Published episodes cannot be modified directly.",
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    try:
        metadata = validate_artwork(
            slot=slot,
            file_bytes=file_bytes,
            content_type=file.content_type or "",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    existing = (
        db.query(Artwork)
        .filter(
            Artwork.episode_id == episode_id,
            Artwork.slot == slot,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                f"{slot} artwork already exists "
                "for this episode."
            ),
        )

    original_filename = file.filename or "artwork"
    filename = Path(original_filename).name

    if not filename:
        filename = "artwork"

    object_key = (
        f"episodes/"
        f"{episode.episode_id}/"
        f"{slot}/"
        f"{filename}"
    )

    try:
        storage.save(
            object_key=object_key,
            data=file_bytes,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to save artwork file.",
        ) from exc

    artwork = Artwork(
        episode_id=episode_id,
        slot=slot,
        object_key=object_key,
        width=metadata["width"],
        height=metadata["height"],
        size_bytes=metadata["size_bytes"],
        content_type=metadata["content_type"],
    )

    db.add(artwork)

    try:
        db.commit()
        db.refresh(artwork)

    except IntegrityError as exc:
        db.rollback()

        try:
            stored_path = storage.get_path(object_key)

            if stored_path.exists():
                stored_path.unlink()

        except OSError:
            pass

        raise HTTPException(
            status_code=409,
            detail=(
                "Artwork conflicts with an existing "
                "artwork record."
            ),
        ) from exc

    except Exception as exc:
        db.rollback()

        try:
            stored_path = storage.get_path(object_key)

            if stored_path.exists():
                stored_path.unlink()

        except OSError:
            pass

        raise HTTPException(
            status_code=500,
            detail="Failed to save artwork metadata.",
        ) from exc

    return {
        "message": "Artwork uploaded successfully.",
        "artwork": artwork_response(artwork),
    }


@router.get("/file/{object_key:path}")
def get_artwork_file(
    object_key: str,
    db: Session = Depends(get_db),
):
    artwork = (
        db.query(Artwork)
        .filter(Artwork.object_key == object_key)
        .first()
    )

    if artwork is None:
        raise HTTPException(
            status_code=404,
            detail="Artwork not found.",
        )

    try:
        path = storage.get_path(object_key)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Artwork file not found.",
        )

    return FileResponse(
        path,
        media_type=artwork.content_type,
        filename=Path(object_key).name,
    )