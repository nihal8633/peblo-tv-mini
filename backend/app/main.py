from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.models import Artwork, Episode, PublishRun, Season, Show

from app.routers import (
    artworks,
    auth,
    catalog,
    episodes,
    publish,
    search,
    seasons,
    shows,
    validation,
)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

# Create database tables if they do not already exist.
Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Peblo TV Mini API",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "peblo-tv-mini-api",
    }


# ---------------------------------------------------------------------------
# Local storage
# ---------------------------------------------------------------------------

STORAGE_PATH = Path(__file__).resolve().parents[2] / "storage"

STORAGE_PATH.mkdir(
    parents=True,
    exist_ok=True,
)

app.mount(
    "/storage",
    StaticFiles(directory=STORAGE_PATH),
    name="storage",
)


# ---------------------------------------------------------------------------
# API routers
# ---------------------------------------------------------------------------

app.router.include_router(auth.router)
app.router.include_router(shows.router)
app.router.include_router(episodes.router)
app.router.include_router(artworks.router)
app.router.include_router(validation.router)
app.router.include_router(publish.router)
app.router.include_router(catalog.router)
app.router.include_router(search.router)
app.router.include_router(seasons.router)