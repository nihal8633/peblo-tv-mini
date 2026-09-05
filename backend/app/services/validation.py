import json
from io import BytesIO
from pathlib import Path

from PIL import Image


DATA_FILE = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "seed_shows.json"
)

MAX_ARTWORK_SIZE = 200 * 1024

ARTWORK_RULES = {
    "poster": (600, 900),
    "banner": (1280, 720),
    "thumbnail": (640, 360),
}

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


def load_seed_data():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def validate_records(records):
    errors = []
    warnings = []
    seen_groups = {}

    for record in records:
        episode_id = record.get("episode_id")
        content_group = record.get("content_group")
        language = record.get("language")
        status = record.get("status")
        duration = record.get("duration_seconds")
        artwork = record.get("artwork_available") or []
        season_number = record.get("season_number")
        section = record.get("section")
        categories = record.get("categories") or []

        if not episode_id:
            errors.append({
                "episode_id": episode_id,
                "message": "Episode is missing episode_id",
            })
            continue

        if not content_group:
            errors.append({
                "episode_id": episode_id,
                "message": "Episode is missing content_group",
            })

        if language not in ALLOWED_LANGUAGES:
            errors.append({
                "episode_id": episode_id,
                "message": (
                    f"Invalid language '{language}'. "
                    f"Allowed languages: {', '.join(sorted(ALLOWED_LANGUAGES))}"
                ),
            })

        if status not in {"draft", "published"}:
            errors.append({
                "episode_id": episode_id,
                "message": f"Invalid episode status: {status}",
            })

        if status == "published":
            if duration is None or duration <= 0:
                errors.append({
                    "episode_id": episode_id,
                    "message": "Published episode has no valid duration",
                })

            if not artwork:
                errors.append({
                    "episode_id": episode_id,
                    "message": "Published episode has no artwork",
                })

        if content_group and language:
            group_key = (content_group, language)

            if group_key in seen_groups:
                errors.append({
                    "episode_id": episode_id,
                    "message": (
                        f"Duplicate (content_group, language): "
                        f"{content_group}, {language}. "
                        f"Already used by {seen_groups[group_key]}"
                    ),
                })
            else:
                seen_groups[group_key] = episode_id

        if season_number == 0:
            warnings.append({
                "episode_id": episode_id,
                "message": (
                    "Season 0 trailer content will not appear "
                    "as a normal viewer season"
                ),
            })

        if section is not None and section not in ALLOWED_SECTIONS:
            errors.append({
                "episode_id": episode_id,
                "message": (
                    f"Invalid section '{section}'. "
                    f"Allowed sections: "
                    f"{', '.join(sorted(ALLOWED_SECTIONS))}"
                ),
            })

        invalid_categories = [
            category
            for category in categories
            if category not in ALLOWED_CATEGORIES
        ]

        if invalid_categories:
            errors.append({
                "episode_id": episode_id,
                "message": (
                    "Invalid categories: "
                    + ", ".join(sorted(set(invalid_categories)))
                ),
            })

    return {
        "total_records": len(records),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def validate_artwork(
    slot: str,
    file_bytes: bytes,
    content_type: str,
):
    if slot not in ARTWORK_RULES:
        raise ValueError(
            "Invalid artwork slot. Use poster, banner, or thumbnail."
        )

    if len(file_bytes) > MAX_ARTWORK_SIZE:
        raise ValueError(
            "Artwork file is too large. Maximum allowed size is 200 KB."
        )

    if not content_type or not content_type.startswith("image/"):
        raise ValueError(
            "Invalid file type. Please upload an image."
        )

    try:
        image = Image.open(BytesIO(file_bytes))
        image.verify()

        image = Image.open(BytesIO(file_bytes))
        width, height = image.size

    except Exception as exc:
        raise ValueError(
            "The uploaded file is not a valid image."
        ) from exc

    expected_width, expected_height = ARTWORK_RULES[slot]

    if width != expected_width or height != expected_height:
        raise ValueError(
            f"Invalid {slot} dimensions. "
            f"Expected {expected_width}x{expected_height}, "
            f"received {width}x{height}."
        )

    return {
        "width": width,
        "height": height,
        "size_bytes": len(file_bytes),
        "content_type": content_type,
    }