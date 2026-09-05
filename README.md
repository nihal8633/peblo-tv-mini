# Peblo TV Mini

A small CMS → API → publish pipeline → catalogue → viewer implementation for the Peblo TV take-home assignment.

## Architecture

- **CMS:** React + Vite. Editors manage shows, seasons, episodes and artwork; admins can publish.
- **API:** FastAPI + SQLAlchemy + PostgreSQL for authentication, authorization, validation, search and publishing.
- **Storage:** Local filesystem behind a storage abstraction. Production can replace this with Cloudflare R2 without changing the content workflow.
- **Viewer:** Separate React app that reads the published `catalogue.json`, not CMS/admin APIs.
- **Publishing:** Builds a deterministic catalogue from published content and atomically replaces the previous catalogue.

## Run locally

```bash
docker compose up --build