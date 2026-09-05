import json
import os
import tempfile
from collections import defaultdict
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Episode, Season, Show


CATALOG_PATH = (
    Path(__file__).resolve().parents[3] / "storage" / "catalogue.json"
)

SECTION_ORDER = {
    "featured": 0,
    "series": 1,
    "minisodes": 2,
    "songs": 3,
}

LANGUAGE_ORDER = {
    "en": 0,
    "hi": 1,
}


def artwork_for_episode(episode):
    artwork = {}

    for item in episode.artworks:
        artwork[item.slot] = {
            "object_key": item.object_key,
            "url": f"/storage/{item.object_key}",
            "width": item.width,
            "height": item.height,
        }

    return artwork


def build_episode_group(episodes):
    ordered_episodes = sorted(
        episodes,
        key=lambda episode: (
            LANGUAGE_ORDER.get(episode.language, 999),
            episode.language,
            episode.id,
        ),
    )

    first_episode = ordered_episodes[0]

    languages = []
    artwork_by_language = {}

    for episode in ordered_episodes:
        if episode.language not in languages:
            languages.append(episode.language)

        artwork_by_language[episode.language] = artwork_for_episode(
            episode
        )

    default_artwork = artwork_by_language.get(
        first_episode.language,
        {},
    )

    return {
        "content_group": first_episode.content_group,
        "episode_number": first_episode.episode_number,
        "title": first_episode.title,
        "duration_seconds": first_episode.duration_seconds,
        "languages": languages,
        "categories": first_episode.categories or [],
        "artwork": default_artwork,
        "artwork_by_language": artwork_by_language,
    }


def build_catalogue(db: Session):
    shows = db.scalars(
        select(Show)
        .where(
            Show.status == "published",
            Show.section.is_not(None),
        )
        .order_by(
            Show.section,
            Show.title,
            Show.id,
        )
    ).all()

    sections = defaultdict(list)

    for show in shows:
        seasons = db.scalars(
            select(Season)
            .where(
                Season.show_id == show.id,
                Season.season_number != 0,
            )
            .order_by(Season.season_number)
        ).all()

        show_entry = {
            "slug": show.slug,
            "title": show.title,
            "synopsis": show.synopsis,
            "section": show.section,
            "seasons": [],
        }

        for season in seasons:
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

            grouped = defaultdict(list)

            for episode in episodes:
                grouped[episode.content_group].append(
                    episode
                )

            catalogue_episodes = []

            for content_group in sorted(
                grouped,
                key=lambda value: (
                    grouped[value][0].episode_number,
                    value,
                ),
            ):
                catalogue_episodes.append(
                    build_episode_group(
                        grouped[content_group]
                    )
                )

            show_entry["seasons"].append(
                {
                    "season_number": season.season_number,
                    "episodes": catalogue_episodes,
                }
            )

        # IMPORTANT:
        # Add the completed show to its section.
        sections[show.section].append(show_entry)

    ordered_sections = []

    for section_name in sorted(
        sections,
        key=lambda value: SECTION_ORDER.get(
            value,
            999,
        ),
    ):
        ordered_sections.append(
            {
                "section": section_name,
                "shows": sorted(
                    sections[section_name],
                    key=lambda show: (
                        show["title"].lower(),
                        show["slug"],
                    ),
                ),
            }
        )

    return {
        "version": 1,
        "sections": ordered_sections,
    }


def write_catalogue_atomic(catalogue):
    CATALOG_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fd, temp_path = tempfile.mkstemp(
        prefix="catalogue-",
        suffix=".json",
        dir=CATALOG_PATH.parent,
    )

    try:
        with os.fdopen(
            fd,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                catalogue,
                file,
                ensure_ascii=False,
                indent=2,
                sort_keys=False,
            )

            file.flush()
            os.fsync(file.fileno())

        os.replace(
            temp_path,
            CATALOG_PATH,
        )

    except Exception:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass

        raise