# Peblo TV Mini

CMS → FastAPI/PostgreSQL → publish pipeline → catalogue → viewer.

## Architecture

- **CMS:** React + Vite for shows, seasons, episodes, artwork and publishing.
- **API:** FastAPI + SQLAlchemy + PostgreSQL for CRUD, validation, auth, search and publishing.
- **Storage:** Local filesystem behind a storage abstraction; production can use Cloudflare R2 through the same interface.
- **Viewer:** Separate React app consuming the published `catalogue.json`, not admin APIs.

## Run locally

```bash
docker compose up --build