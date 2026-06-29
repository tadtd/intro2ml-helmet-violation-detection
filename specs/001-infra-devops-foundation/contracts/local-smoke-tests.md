# Contract: Local Smoke Tests

## Preconditions

- Real local credentials are present only in untracked `.env`.
- `docker compose up --build` starts `redis`, `api`, and `worker`.
- A developer has an authenticated test token or documented login path for the
  upload endpoint.

## Required Checks

| Check | Command/Action | Passing Result |
|-------|----------------|----------------|
| Compose services | `docker compose ps` | `redis`, `api`, and `worker` are running |
| API health | `Invoke-RestMethod http://localhost:8000/health` | Health payload is returned without error |
| Authenticated upload | Submit a small test video to `POST /videos/upload` | Request succeeds and returns/creates video metadata |
| Supabase row | Inspect `videos` table for uploaded item | Row exists with expected filename/status |
| Storage object | Inspect private `videos` bucket | Uploaded object exists |
| Worker readiness | `docker compose logs worker` or `docker compose ps worker` | Worker process is running and connected enough for local queue readiness |

## Non-Goals

- Full model inference.
- Violation crop generation.
- Frontend upload workflow validation.
- Production deployment execution.
