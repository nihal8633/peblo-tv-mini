from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import require_editor
from app.services.publish import validate_for_publish


router = APIRouter(
    prefix="/validation",
    tags=["Validation"],
)


@router.get("/report")
def validation_report(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    errors = validate_for_publish(db)

    return {
        "valid": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
    }