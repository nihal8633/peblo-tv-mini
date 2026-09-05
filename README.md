# Peblo TV Mini

A small CMS → API → publish pipeline → catalogue → viewer implementation for the Peblo TV take-home assignment.

## Architecture

- **CMS:** React + Vite. Editors manage shows, seasons, episodes and artwork; admins can publish.
- **API:** FastAPI + SQLAlchemy + PostgreSQL. Handles authentication, authorization, validation, search and publishing.
- **Storage:** Local filesystem abstraction for the demo. The storage interface can be replaced by Cloudflare R2 without changing the content workflow.
- **Viewer:** Separate React app that reads the published `catalogue.json` rather than admin APIs.
- **Publishing:** Builds a deterministic catalogue from published content and atomically replaces the previous catalogue.

## Run locally

The complete stack can be started with:

```bash
docker compose up --build