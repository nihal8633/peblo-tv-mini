from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


router = APIRouter(
    prefix="/catalog",
    tags=["Catalog"],
)


CATALOG_PATH = (
    Path(__file__).resolve().parents[3]
    / "storage"
    / "catalogue.json"
)


@router.get("")
def get_catalog():
    if not CATALOG_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Published catalogue is not available yet.",
        )

    return FileResponse(
        CATALOG_PATH,
        media_type="application/json",
        filename="catalogue.json",
    )