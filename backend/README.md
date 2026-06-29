# Helmet Violation Detection Backend

FastAPI API plus Celery worker for video processing and live camera inference.

## Local Setup

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Run Redis from the repository root:

```bash
docker compose up redis
```

Run a worker in a second terminal:

```bash
cd backend
uv run celery -A app.celery_app.celery_app worker --loglevel=info
```

## Environment

Copy `../.env.example` to `.env` or provide the variables in your shell. Supabase-backed routes need:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET`
- `SUPABASE_VIDEO_BUCKET` for uploaded source videos
- `SUPABASE_STORAGE_BUCKET` for violation crop images

## Supabase Schema

Run the SQL modules in `supabase/schema/` in numeric order from the Supabase SQL
editor. Detailed setup, bucket policy, auth, realtime, verification, and
rollback guidance is maintained in `../docs/supabase-setup.md`.

Create two storage buckets before testing uploads:

- `videos`
- `violations`

The API exposes:

- `GET /health`
- `POST /videos/upload`
- `GET /violations`
- `WS /ws/camera`
