from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Artwork, Episode, PublishRun, Season, Show
from app.services.catalog import (
    build_catalogue,
    write_catalogue_atomic,
)
from app.services.validation import (
    ARTWORK_RULES,
    MAX_ARTWORK_SIZE,
)


VALID_SECTIONS = {
    "featured",
    "series",
    "minisodes",
    "songs",
}

VALID_LANGUAGES = {
    "en",
    "hi",
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


def validate_for_publish(db: Session):
    errors = []

    shows = db.scalars(
        select(Show)
        .where(Show.status == "published")
        .order_by(Show.id)
    ).all()

    seen_groups = {}

    for show in shows:
        if not show.section:
            errors.append(
                f"Show '{show.title}' is published but has no section."
            )
        elif show.section not in VALID_SECTIONS:
            errors.append(
                f"Show '{show.title}' has invalid section "
                f"'{show.section}'."
            )

        seasons = db.scalars(
            select(Season)
            .where(Season.show_id == show.id)
            .order_by(
                Season.season_number,
                Season.id,
            )
        ).all()

        for season in seasons:

            # Season 0 is trailer-only content and is not
            # exposed as a normal viewer season.
            if season.season_number == 0:
                continue

            episodes = db.scalars(
                select(Episode)
                .where(
                    Episode.season_id == season.id,
                    Episode.status == "published",
                )
                .order_by(
                    Episode.episode_number,
                    Episode.id,
                )
            ).all()

            for episode in episodes:

                if (
                    episode.duration_seconds is None
                    or episode.duration_seconds <= 0
                ):
                    errors.append(
                        f"Episode '{episode.episode_id}' is "
                        "published but has no valid duration."
                    )

                if episode.language not in VALID_LANGUAGES:
                    errors.append(
                        f"Episode '{episode.episode_id}' has invalid "
                        f"language '{episode.language}'."
                    )

                if not episode.content_group.strip():
                    errors.append(
                        f"Episode '{episode.episode_id}' has an empty "
                        "content_group."
                    )

                group_key = (
                    episode.content_group,
                    episode.language,
                )

                previous_episode_id = seen_groups.get(
                    group_key
                )

                if previous_episode_id is not None:
                    errors.append(
                        f"Duplicate (content_group, language): "
                        f"{episode.content_group}, "
                        f"{episode.language}. "
                        f"Already used by "
                        f"{previous_episode_id}."
                    )
                else:
                    seen_groups[group_key] = (
                        episode.episode_id
                    )

                artworks = db.scalars(
                    select(Artwork)
                    .where(
                        Artwork.episode_id == episode.id
                    )
                ).all()

                artwork_by_slot = {
                    artwork.slot: artwork
                    for artwork in artworks
                }

                missing = (
                    REQUIRED_ARTWORK_SLOTS
                    - set(artwork_by_slot)
                )

                if missing:
                    errors.append(
                        f"Episode '{episode.episode_id}' is "
                        f"missing artwork: "
                        f"{', '.join(sorted(missing))}."
                    )

                for slot, artwork in artwork_by_slot.items():

                    expected_dimensions = ARTWORK_RULES.get(
                        slot
                    )

                    if expected_dimensions is None:
                        errors.append(
                            f"Episode '{episode.episode_id}' has "
                            f"invalid artwork slot '{slot}'."
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
                            f"Episode '{episode.episode_id}' has "
                            f"invalid {slot} artwork dimensions. "
                            f"Expected "
                            f"{expected_width}x{expected_height}, "
                            f"received "
                            f"{artwork.width}x{artwork.height}."
                        )

                    if artwork.size_bytes > MAX_ARTWORK_SIZE:
                        errors.append(
                            f"Episode '{episode.episode_id}' has "
                            f"{slot} artwork larger than 200 KB."
                        )

                    if artwork.content_type not in (
                        VALID_IMAGE_CONTENT_TYPES
                    ):
                        errors.append(
                            f"Episode '{episode.episode_id}' has "
                            f"invalid {slot} artwork content type "
                            f"'{artwork.content_type}'."
                        )

    return errors


def publish_catalogue(
    db: Session,
    triggered_by: str = "admin",
):
    errors = validate_for_publish(db)

    publish_run = PublishRun(
        triggered_by=triggered_by,
        status="started",
        published_count=0,
        error_count=len(errors),
    )

    db.add(publish_run)
    db.commit()
    db.refresh(publish_run)

    if errors:
        publish_run.status = "failed"
        publish_run.completed_at = datetime.now(
            timezone.utc
        )
        publish_run.message = "\n".join(errors)

        db.commit()

        return {
            "success": False,
            "publish_run_id": publish_run.id,
            "published_count": 0,
            "error_count": len(errors),
            "errors": errors,
        }

    try:
        catalogue = build_catalogue(db)

        published_show_count = sum(
            len(section["shows"])
            for section in catalogue["sections"]
        )

        published_episode_count = sum(
            len(season["episodes"])
            for section in catalogue["sections"]
            for show in section["shows"]
            for season in show["seasons"]
        )

        write_catalogue_atomic(catalogue)

        publish_run.status = "success"
        publish_run.completed_at = datetime.now(
            timezone.utc
        )
        publish_run.published_count = (
            published_episode_count
        )
        publish_run.error_count = 0
        publish_run.message = (
            "Catalogue published successfully. "
            f"{published_show_count} shows, "
            f"{published_episode_count} episodes."
        )

        db.commit()

        return {
            "success": True,
            "publish_run_id": publish_run.id,
            "published_count": published_episode_count,
            "published_show_count": published_show_count,
            "published_episode_count": (
                published_episode_count
            ),
            "error_count": 0,
        }

    except Exception as exc:
        db.rollback()

        # The catalogue writer uses an atomic replacement.
        # Therefore a failed write cannot leave a partially
        # written live catalogue.

        publish_run = db.get(
            PublishRun,
            publish_run.id,
        )

        if publish_run is not None:
            publish_run.status = "failed"
            publish_run.completed_at = datetime.now(
                timezone.utc
            )
            publish_run.error_count = 1
            publish_run.message = str(exc)

            db.commit()

        return {
            "success": False,
            "publish_run_id": (
                publish_run.id
                if publish_run is not None
                else None
            ),
            "published_count": 0,
            "error_count": 1,
            "errors": [str(exc)],
        }