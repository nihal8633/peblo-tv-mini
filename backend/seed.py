import json
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Episode, Season, Show
from app.services.validation import validate_records


DATA_FILE = Path(__file__).parent / "data" / "seed_shows.json"


def load_seed_data():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def import_valid_records(records, errors):
    invalid_episode_ids = {
        error["episode_id"]
        for error in errors
        if error.get("episode_id")
    }

    db = SessionLocal()

    imported = 0
    skipped = 0

    try:
        for record in records:
            episode_id = record["episode_id"]

            if episode_id in invalid_episode_ids:
                skipped += 1
                continue

            show = db.scalar(
                select(Show).where(
                    Show.slug == record["slug"]
                )
            )

            if show is None:
                show = Show(
                    slug=record["slug"],
                    title=record["show_title"],
                    synopsis=record["synopsis"],
                    section=record.get("section"),
                    status=(
                        "published"
                        if record["status"] == "published"
                        else "draft"
                    ),
                )

                db.add(show)
                db.flush()

            elif (
                record["status"] == "published"
                and show.status != "published"
            ):
                show.status = "published"

            season = db.scalar(
                select(Season).where(
                    Season.show_id == show.id,
                    Season.season_number == record["season_number"],
                )
            )

            if season is None:
                season = Season(
                    show_id=show.id,
                    season_number=record["season_number"],
                )

                db.add(season)
                db.flush()

            existing = db.scalar(
                select(Episode).where(
                    Episode.episode_id == episode_id
                )
            )

            if existing is not None:
                skipped += 1
                continue

            episode = Episode(
                episode_id=episode_id,
                season_id=season.id,
                episode_number=record["episode_number"],
                title=record["episode_title"],
                duration_seconds=record.get("duration_seconds"),
                language=record["language"],
                content_group=record["content_group"],
                status=record["status"],
                categories=record.get("categories", []),
            )

            db.add(episode)
            imported += 1

        db.commit()
        return imported, skipped

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def main():
    records = load_seed_data()

    print(f"Loaded {len(records)} seed records\n")

    report = validate_records(records)

    print("VALIDATION REPORT")
    print("=" * 60)
    print(f"Errors:   {report['error_count']}")
    print(f"Warnings: {report['warning_count']}\n")

    if report["errors"]:
        print("ERRORS")
        print("-" * 60)

        for error in report["errors"]:
            print(
                f"- {error['episode_id']}: "
                f"{error['message']}"
            )

        print()

    if report["warnings"]:
        print("WARNINGS")
        print("-" * 60)

        for warning in report["warnings"]:
            print(
                f"- {warning['episode_id']}: "
                f"{warning['message']}"
            )

        print()

    imported, skipped = import_valid_records(
        records,
        report["errors"],
    )

    print("IMPORT RESULT")
    print("-" * 60)
    print(f"Imported: {imported}")
    print(f"Skipped:  {skipped}")
    print("\nSeed import completed successfully.")


if __name__ == "__main__":
    main()