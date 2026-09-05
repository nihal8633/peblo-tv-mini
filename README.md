# Peblo TV Mini

CMS → FastAPI/PostgreSQL → publish pipeline → catalogue → viewer.

## Architecture

- CMS: React + Vite for shows, seasons, episodes, artwork and publishing.
- API: FastAPI + SQLAlchemy + PostgreSQL for CRUD, validation, authentication, search and publishing.
- Storage: Local filesystem behind a storage abstraction; production can use Cloudflare R2.
- Viewer: Separate React app consuming the published `catalogue.json`, not admin APIs.

## Run locally

```bash
docker compose up --build

CMS: http://localhost:5173
Viewer: http://localhost:5174
API/docs: http://localhost:8000/docs

Demo credentials: admin/admin123 and editor/editor123.

Publishing

All published content and artwork are validated before publishing. The catalogue is written to a temporary file, flushed and fsynced, then atomically replaced using os.replace.

Readers therefore see either the previous complete catalogue or the new complete catalogue. If publishing dies before replacement, the previous catalogue remains intact. Publish runs record the triggering user, timestamps, status, counts and errors.

The viewer uses a pre-published catalogue so the public read path is simple, cacheable and decoupled from CMS APIs. The trade-off is that changes appear only after a successful publish.

Validation

Server-side validation enforces artwork dimensions and the 200 KB limit, required artwork and duration for published episodes, valid sections/languages/categories, and unique (content_group, language) variants.

English/Hindi variants sharing a content_group collapse into one catalogue episode with a languages list. Season 0 trailers are excluded from normal viewer seasons.

Editor/admin permissions are enforced by the API.

Search and scale

Search runs server-side through FastAPI/SQLAlchemy with show-title, episode-title and category matching, composable section/category/language filters and pagination.

For a larger catalogue, PostgreSQL indexes/full-text search or a dedicated search service would be preferable to browser-side whole-catalogue searching.

CI / Operability

GitHub Actions runs backend tests and migrations, CMS lint/build, Viewer lint/build, Docker image builds and a deployment placeholder. /health provides container health checking.

Trade-offs / omissions

The take-home uses local storage and demo credentials for reproducibility. Production additions would include R2, managed secrets, versioned catalogue rollback, dry-run publish diffs, richer audit logging and a production deployment target.

AI usage

AI was used for implementation guidance, debugging, test ideas and review. Suggestions were reviewed and tested locally and in GitHub Actions; incorrect suggestions were rejected or corrected.