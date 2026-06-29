# DevOps Local Smoke Test

This runbook proves the local Redis, FastAPI API, Celery worker, and
Supabase-backed upload path are wired together. It does not validate ML
inference, violation crop generation, Kubernetes, CI/CD, or frontend workflows.

## Prerequisites

- Docker Desktop or Docker Engine with Compose.
- Supabase development project configured with `docs/supabase-setup.md`.
- Local credentials in untracked `.env`.
- PowerShell from the repository root.
- A small local MP4 test file, for example `data\sample-smoke.mp4`.
- A local authenticated Supabase user JWT for the upload endpoint.

## Local Environment Safety

Create local environment values from the example file:

```powershell
Copy-Item .env.example .env
notepad .env
```

Required local values:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET`
- `SUPABASE_VIDEO_BUCKET=videos`
- `SUPABASE_STORAGE_BUCKET=violations`
- `REDIS_URL`

Keep real `.env` files, service-role keys, JWTs, kubeconfigs, certificates, and
private keys out of git. Frontend values may only use anon or publishable
credentials.

## Start Compose

Start Redis, API, and worker from the repository root:

```powershell
docker compose up --build
```

In a second PowerShell session, check service state:

```powershell
docker compose ps
```

Expected result: `redis`, `api`, and `worker` are present. Redis should become
healthy, the API should expose port `8000`, and the worker should remain
running.

## Health Check

```powershell
Invoke-RestMethod -Uri http://localhost:8000/health -Method Get
```

Expected result: the command returns the API health payload without an exception.

## Authenticated Upload Check

Set the token and video path in your shell. The JWT must belong to a development
Supabase user. Keep this token in your shell only; do not add a real JWT to
`.env` or `.env.example`.

```powershell
$env:LOCAL_SUPABASE_USER_JWT = "<LOCAL_SUPABASE_USER_JWT>"
$VideoPath = "data\sample-smoke.mp4"
Test-Path $VideoPath
```

If `Test-Path` returns `False`, place a small local MP4 at that path or choose a
different local file path.

Submit the upload:

```powershell
curl.exe -X POST "http://localhost:8000/videos/upload" `
  -H "Authorization: Bearer $env:LOCAL_SUPABASE_USER_JWT" `
  -F "model_name=yolo" `
  -F "video=@$VideoPath"
```

Expected result: the API returns JSON with `video_id`, `task_id`, and
`status=queued`.

## Supabase Verification

Use the returned `video_id` to verify Supabase state:

1. Open the Supabase dashboard for the development project.
2. Inspect `public.videos`.
3. Confirm a row exists for the returned `video_id`.
4. Confirm the row has the expected `filename`, `storage_path`, `model_used`,
   and `status`.
5. Inspect the private `videos` storage bucket.
6. Confirm an object exists at the row's `storage_path`.

The `violations` public-read bucket is not required for this upload wiring
smoke test because ML inference and crop generation are out of scope here.

## Worker Readiness

Check the worker process:

```powershell
docker compose ps worker
docker compose logs worker --tail 80
```

Expected result: the worker container is running and logs show the Celery worker
started without Redis connection failures.

## Validation Status Notes

The full upload smoke test requires real local Supabase values and a development
user JWT. If those credentials are unavailable, record that blocker in your
handoff notes and run the non-secret validation that still applies:

```powershell
Copy-Item .env.example .env
docker compose config
Remove-Item .env
```

This parser check does not prove backend health or upload wiring; it only
confirms Compose can resolve the local stack shape without committing secrets.

## Troubleshooting

- Missing env values: confirm `.env` exists and contains local Supabase values.
- API health failure: run `docker compose logs api --tail 80` and confirm the
  API container started.
- Redis connection failure: confirm Compose overrides `REDIS_URL` to
  `redis://redis:6379/0` for API and worker containers.
- Upload returns `401`: refresh `LOCAL_SUPABASE_USER_JWT` for a development user
  and confirm `SUPABASE_JWT_SECRET` matches the Supabase project.
- Upload succeeds but no task appears queued: inspect `docker compose logs api`
  and `docker compose logs worker` for Celery or Redis errors.
- Missing storage object: confirm `SUPABASE_VIDEO_BUCKET=videos`, the bucket is
  private, and the service-role key is backend-only and valid.
- Worker not running: rebuild with `docker compose up --build worker` and check
  `docker compose logs worker --tail 80`.
