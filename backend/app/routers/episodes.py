from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Artwork, Episode, Season
from app.schemas.episode import EpisodeCreate, EpisodeUpdate
from app.security import require_editor
from app.services.validation import ARTWORK_RULES, MAX_ARTWORK_SIZE


router = APIRouter(
    prefix="/episodes",
    tags=["Episodes"],
)


# ---------------------------------------------------------------------------
# Validation constants
# ---------------------------------------------------------------------------

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

ALLOWED_STATUSES = {
    "draft",
    "published",
}

REQUIRED_ARTWORK_SLOTS = {
    "poster",
    "banner",
    "thumbnail",
}

VALID_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_language(language: str):
    if language not in ALLOWED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid language '{language}'. "
                f"Allowed languages: "
                f"{', '.join(sorted(ALLOWED_LANGUAGES))}"
            ),
        )


def validate_categories(categories: list[str]):
    invalid_categories = [
        category
        for category in categories
        if category not in ALLOWED_CATEGORIES
    ]

    if invalid_categories:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid categories: "
                + ", ".join(sorted(set(invalid_categories)))
            ),
        )


def validate_episode_ready_for_publish(
    db: Session,
    episode: Episode,
):
    """
    Validate everything required before an episode can become published.
    """

    errors = []

    # Duration
    if (
        episode.duration_seconds is None
        or episode.duration_seconds <= 0
    ):
        errors.append(
            "Episode must have a valid duration before publishing."
        )

    # Language
    if episode.language not in ALLOWED_LANGUAGES:
        errors.append(
            f"Invalid language '{episode.language}'. "
            f"Allowed languages: "
            f"{', '.join(sorted(ALLOWED_LANGUAGES))}"
        )

    # Content group
    if not episode.content_group.strip():
        errors.append(
            "content_group cannot be blank."
        )

    # Artwork
    artworks = db.scalars(
        select(Artwork).where(
            Artwork.episode_id == episode.id
        )
    ).all()

    artwork_by_slot = {
        artwork.slot: artwork
        for artwork in artworks
    }

    missing_slots = (
        REQUIRED_ARTWORK_SLOTS
        - set(artwork_by_slot.keys())
    )

    if missing_slots:
        errors.append(
            "Missing artwork: "
            + ", ".join(sorted(missing_slots))
            + "."
        )

    # Validate every uploaded artwork record.
    for slot, artwork in artwork_by_slot.items():

        expected_dimensions = ARTWORK_RULES.get(slot)

        if expected_dimensions is None:
            errors.append(
                f"Invalid artwork slot '{slot}'."
            )
            continue

        expected_width, expected_height = (
            expected_dimensions
        )

        if (
            artwork.width != expected_width
            or artwork.height != expected_height
        ):
            errors.append(
                f"{slot} artwork must be "
                f"{expected_width}x{expected_height}; "
                f"received "
                f"{artwork.width}x{artwork.height}."
            )

        if artwork.size_bytes > MAX_ARTWORK_SIZE:
            errors.append(
                f"{slot} artwork is larger than 200 KB."
            )

        if (
            artwork.content_type
            not in VALID_IMAGE_CONTENT_TYPES
        ):
            errors.append(
                f"{slot} artwork has invalid content type "
                f"'{artwork.content_type}'."
            )

    if errors:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Episode is not ready for publishing.",
                "errors": errors,
            },
        )


# ---------------------------------------------------------------------------
# Response helper
# ---------------------------------------------------------------------------

def episode_response(episode: Episode):
    return {
        "id": episode.id,
        "episode_id": episode.episode_id,
        "season_id": episode.season_id,
        "episode_number": episode.episode_number,
        "title": episode.title,
        "duration_seconds": episode.duration_seconds,
        "language": episode.language,
        "content_group": episode.content_group,
        "status": episode.status,
        "categories": episode.categories or [],
    }


# ---------------------------------------------------------------------------
# List episodes
# ---------------------------------------------------------------------------

@router.get("/")
def list_episodes(
    show_id: int | None = None,
    season_number: int | None = None,
    language: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    if language is not None:
        validate_language(language)

    if (
        status is not None
        and status not in ALLOWED_STATUSES
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid status '{status}'. "
                f"Allowed statuses: "
                f"{', '.join(sorted(ALLOWED_STATUSES))}"
            ),
        )

    query = select(Episode).join(Season)

    if show_id is not None:
        query = query.where(
            Season.show_id == show_id
        )

    if season_number is not None:
        query = query.where(
            Season.season_number == season_number
        )

    if language:
        query = query.where(
            Episode.language == language
        )

    if status:
        query = query.where(
            Episode.status == status
        )

    query = query.order_by(
        Season.show_id,
        Season.season_number,
        Episode.episode_number,
        Episode.id,
    )

    offset = (page - 1) * page_size

    episodes = db.scalars(
        query.offset(offset).limit(page_size)
    ).all()

    return {
        "page": page,
        "page_size": page_size,
        "count": len(episodes),
        "items": [
            episode_response(episode)
            for episode in episodes
        ],
    }


# ---------------------------------------------------------------------------
# Get episode
# ---------------------------------------------------------------------------

@router.get("/{episode_id}")
def get_episode(
    episode_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    episode = db.get(Episode, episode_id)

    if episode is None:
        raise HTTPException(
            status_code=404,
            detail="Episode not found",
        )

    return episode_response(episode)


# ---------------------------------------------------------------------------
# Create episode
# ---------------------------------------------------------------------------

@router.post("/", status_code=201)
def create_episode(
    data: EpisodeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    # Make sure the season exists.
    season = db.get(
        Season,
        data.season_id,
    )

    if season is None:
        raise HTTPException(
            status_code=404,
            detail="Season not found",
        )

    validate_language(data.language)
    validate_categories(data.categories)

    if data.status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="status must be 'draft' or 'published'",
        )

    # New episodes must always start as drafts.
    if data.status == "published":
        raise HTTPException(
            status_code=400,
            detail=(
                "Episode cannot be created directly as published. "
                "Create it as draft, add artwork, then publish it."
            ),
        )

    episode_id = data.episode_id.strip()
    title = data.title.strip()
    content_group = data.content_group.strip()

    if not episode_id or not title or not content_group:
        raise HTTPException(
            status_code=400,
            detail=(
                "episode_id, title, and content_group "
                "cannot be blank."
            ),
        )

    # Unique episode ID.
    existing_episode = db.scalar(
        select(Episode).where(
            Episode.episode_id == episode_id
        )
    )

    if existing_episode is not None:
        raise HTTPException(
            status_code=409,
            detail="episode_id already exists",
        )

    # Unique language variant.
    duplicate_variant = db.scalar(
        select(Episode).where(
            Episode.content_group == content_group,
            Episode.language == data.language,
        )
    )

    if duplicate_variant is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Duplicate (content_group, language) "
                f"already used by "
                f"{duplicate_variant.episode_id}"
            ),
        )

    episode = Episode(
        episode_id=episode_id,
        season_id=data.season_id,
        episode_number=data.episode_number,
        title=title,
        duration_seconds=data.duration_seconds,
        language=data.language,
        content_group=content_group,
        status="draft",
        categories=data.categories,
    )

    db.add(episode)

    try:
        db.commit()
        db.refresh(episode)

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Episode conflicts with an existing record",
        ) from exc

    return episode_response(episode)


# ---------------------------------------------------------------------------
# Update episode
# ---------------------------------------------------------------------------

@router.patch("/{episode_id}")
def update_episode(
    episode_id: int,
    data: EpisodeUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    episode = db.get(
        Episode,
        episode_id,
    )

    if episode is None:
        raise HTTPException(
            status_code=404,
            detail="Episode not found",
        )

    # Published episodes are immutable through normal editing.
    if episode.status == "published":
        raise HTTPException(
            status_code=409,
            detail=(
                "Published episodes cannot be edited directly."
            ),
        )

    updates = data.model_dump(
        exclude_unset=True
    )

    # -------------------------------------------------------
    # Publishing
    # -------------------------------------------------------

    if "status" in updates:

        if updates["status"] not in ALLOWED_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="status must be 'draft' or 'published'",
            )

        if updates["status"] == "published":

            # Only admins can publish.
            if current_user.get("role") != "admin":
                raise HTTPException(
                    status_code=403,
                    detail="Admin role required to publish episodes.",
                )

            # Validate duration, artwork and metadata.
            validate_episode_ready_for_publish(
                db,
                episode,
            )

    # -------------------------------------------------------
    # Language
    # -------------------------------------------------------

    if "language" in updates:
        validate_language(
            updates["language"]
        )

    # -------------------------------------------------------
    # Categories
    # -------------------------------------------------------

    if "categories" in updates:
        validate_categories(
            updates["categories"] or []
        )

    # -------------------------------------------------------
    # Content group
    # -------------------------------------------------------

    new_language = updates.get(
        "language",
        episode.language,
    )

    new_content_group = updates.get(
        "content_group",
        episode.content_group,
    )

    if "content_group" in updates:

        new_content_group = (
            new_content_group.strip()
        )

        if not new_content_group:
            raise HTTPException(
                status_code=400,
                detail="content_group cannot be blank.",
            )

        updates["content_group"] = (
            new_content_group
        )

    # Check duplicate variant when either
    # content_group or language changes.
    if (
        new_language != episode.language
        or new_content_group != episode.content_group
    ):
        duplicate_variant = db.scalar(
            select(Episode).where(
                Episode.content_group
                == new_content_group,
                Episode.language
                == new_language,
                Episode.id != episode.id,
            )
        )

        if duplicate_variant is not None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Duplicate (content_group, language) "
                    f"already used by "
                    f"{duplicate_variant.episode_id}"
                ),
            )

    # -------------------------------------------------------
    # Title
    # -------------------------------------------------------

    if "title" in updates:

        title = updates["title"].strip()

        if not title:
            raise HTTPException(
                status_code=400,
                detail="Title cannot be blank.",
            )

        updates["title"] = title

    # -------------------------------------------------------
    # Apply changes
    # -------------------------------------------------------

    for field, value in updates.items():
        setattr(
            episode,
            field,
            value,
        )

    try:
        db.commit()
        db.refresh(episode)

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Episode conflicts with an existing record",
        ) from exc

    return episode_response(episode)


# ---------------------------------------------------------------------------
# Delete episode
# ---------------------------------------------------------------------------

@router.delete("/{episode_id}")
def delete_episode(
    episode_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    episode = db.get(
        Episode,
        episode_id,
    )

    if episode is None:
        raise HTTPException(
            status_code=404,
            detail="Episode not found",
        )

    if episode.status == "published":
        raise HTTPException(
            status_code=400,
            detail=(
                "Published episodes cannot be deleted directly."
            ),
        )

    db.delete(episode)
    db.commit()

    return {
        "message": "Episode deleted successfully",
        "episode_id": episode.episode_id,
    }