# Helmet Violation Detection Backend

FastAPI API plus Celery worker for video processing and live camera inference.

## Local Setup

Run Redis from the repository root:

```bash
docker compose up redis
```

Run the API locally:

```bash
cd backend
uv sync
REDIS_URL=redis://localhost:6379/0 \
uv run uvicorn app.main:app --reload
```

Run a worker in a second terminal:

```bash
cd backend
REDIS_URL=redis://localhost:6379/0 \
uv run celery -A app.celery_app.celery_app worker --loglevel=info
```

Check the API:

```bash
curl http://localhost:8000/health
```

## Environment

Copy `../.env.example` to `.env` or provide the variables in your shell. Supabase-backed routes need:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET`
- `SUPABASE_VIDEO_BUCKET` for uploaded source videos
- `SUPABASE_STORAGE_BUCKET` for violation crop images

Use this Redis URL when running the backend directly on the host:

```bash
REDIS_URL=redis://localhost:6379/0
```

Use this Redis URL only inside Docker Compose:

```bash
REDIS_URL=redis://redis:6379/0
```

## Supabase Schema

The canonical schema is managed by Supabase CLI migrations in `../supabase/migrations/`.
Run this from the repository root:

```bash
npx supabase db push
```

Database pgTAP tests and benchmark seed SQL live in `../supabase/tests/`.
The migrations create the `videos` and `violations` storage buckets.

The API exposes:

- `GET /health`
- `POST /videos/upload`
- `GET /violations`
- `WS /ws/camera`

Current implementation status:

- `GET /health` works without Supabase.
- `POST /videos/upload` and `GET /violations` require Supabase credentials and JWT auth.
- `WS /ws/camera` currently accepts frames and returns a placeholder response.
- Celery `process_video` is registered, but video processing is still `not_implemented`.
- Model inference is available through `from app.models import run_inference`.
