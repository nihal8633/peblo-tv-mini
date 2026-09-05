import sys
from io import BytesIO
from pathlib import Path

# Make the backend/app package importable when this script
# is executed from the scripts directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from PIL import Image, ImageDraw
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Artwork, Episode
from app.services.storage.local import LocalStorage


STORAGE_ROOT = PROJECT_ROOT / "storage"

storage = LocalStorage(str(STORAGE_ROOT))

ARTWORK_SPECS = {
    "poster": (600, 900),
    "banner": (1280, 720),
    "thumbnail": (640, 360),
}


def create_placeholder(width: int, height: int, text: str) -> bytes:
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    draw.text(
        (40, 40),
        text,
        fill="black",
    )

    output = BytesIO()
    image.save(
        output,
        format="JPEG",
        quality=80,
    )

    return output.getvalue()


def main():
    db = SessionLocal()

    try:
        episodes = db.scalars(
            select(Episode)
            .where(Episode.status == "published")
            .order_by(Episode.id)
        ).all()

        created = 0
        skipped = 0

        for episode in episodes:
            for slot, (width, height) in ARTWORK_SPECS.items():

                existing = db.scalar(
                    select(Artwork).where(
                        Artwork.episode_id == episode.id,
                        Artwork.slot == slot,
                    )
                )

                if existing:
                    skipped += 1
                    continue

                file_bytes = create_placeholder(
                    width,
                    height,
                    f"{episode.episode_id} - {slot}",
                )

                object_key = (
                    f"episodes/{episode.episode_id}/"
                    f"{slot}/placeholder.jpg"
                )

                storage.save(
                    object_key,
                    file_bytes,
                )

                artwork = Artwork(
                    episode_id=episode.id,
                    slot=slot,
                    object_key=object_key,
                    width=width,
                    height=height,
                    size_bytes=len(file_bytes),
                    content_type="image/jpeg",
                )

                db.add(artwork)
                created += 1

        db.commit()

        print(f"Published episodes checked: {len(episodes)}")
        print(f"Artwork records created: {created}")
        print(f"Artwork records skipped: {skipped}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()