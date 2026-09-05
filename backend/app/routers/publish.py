from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import require_admin
from app.services.publish import publish_catalogue


router = APIRouter(
    prefix="/publish",
    tags=["Publish"],
)


@router.post("")
def publish(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return publish_catalogue(
        db,
        triggered_by=current_user["username"],
    )