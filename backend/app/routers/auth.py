from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.config import settings
from app.security import create_access_token


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    if (
        form_data.username == settings.ADMIN_USERNAME
        and form_data.password == settings.ADMIN_PASSWORD
    ):
        role = "admin"

    elif (
        form_data.username == settings.EDITOR_USERNAME
        and form_data.password == settings.EDITOR_PASSWORD
    ):
        role = "editor"

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    token = create_access_token(
        username=form_data.username,
        role=role,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": form_data.username,
        "role": role,
    }