# Quickstart: Infrastructure and DevOps Foundation

## Prerequisites

- Docker Desktop or Docker Engine with Compose.
- A Supabase development project.
- Local credentials stored in untracked `.env`.
- PowerShell from the repository root.

## 1. Configure Local Environment

```powershell
Copy-Item .env.example .env
notepad .env
```

Fill only local development values. Do not commit `.env`.

## 2. Apply Supabase Schema

Run SQL files from `backend/supabase/schema/` in numeric order:

```text
01_profiles.sql
02_videos.sql
03_violations.sql
04_indexes.sql
05_realtime.sql
```

Expected result: `profiles`, `videos`, and `violations` exist with RLS enabled;
indexes and realtime setup are applied without destructive data changes.

## 3. Create Storage Buckets

Create or verify:

```text
videos      private
violations  public-read
```

Expected result: API/worker can write original uploads to `videos`; violation
evidence crops can produce public-read URLs from `violations`.

## 4. Start Local Runtime

```powershell
docker compose up --build
```

In a second PowerShell:

```powershell
docker compose ps
```

Expected result: `redis`, `api`, and `worker` are running.

## 5. Health Smoke Test

```powershell
Invoke-RestMethod -Uri http://localhost:8000/health -Method Get
```

Expected result: the API returns a health payload without error.

## 6. Upload Wiring Smoke Test

Use an authenticated request to upload a small test video to the local API:

```powershell
$token = "<LOCAL_SUPABASE_USER_JWT>"
curl.exe -X POST "http://localhost:8000/videos/upload" `
  -H "Authorization: Bearer $token" `
  -F "model_name=yolo" `
  -F "video=@data/sample-smoke-small.mp4"
```

Expected result:

- Request succeeds.
- A row exists in `videos`.
- A matching object exists in the private `videos` bucket.
- `docker compose ps worker` shows the worker process running.

This smoke test does not require ML inference or violation crop generation.

## 7. Deployment Artifact Review

Review planned production artifacts:

```powershell
Get-ChildItem .\k8s
Get-Content .\k8s\README.md
Get-Content .\.github\workflows\deploy.yml
Get-Item .\.github\deploy.yml | Select-Object FullName,Length
```

Expected result: `k8s/` exists after implementation and contains `README.md`
plus manifests. `.github/workflows/deploy.yml` contains the reviewable
workflow outline. The existing `.github/deploy.yml` is empty/nonstandard and is
not used as the target workflow. Manifests and workflow contain image
placeholders, workload identity or documented secret placeholders, and no real
secret values.

Terraform, Helm, ArgoCD, and External Secrets are not required for this feature.

For manifest review without applying to a cluster:

```powershell
kubectl kustomize .\k8s
```

For deployment handoff details, read `k8s/README.md`. Apply or server-side
dry-run requires a real cluster and secrets created outside git.
