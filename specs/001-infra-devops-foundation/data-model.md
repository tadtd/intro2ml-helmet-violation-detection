# Data Model: Infrastructure and DevOps Foundation

## Development Environment Configuration

**Purpose**: Local-only configuration needed to connect the monorepo to a
Supabase development project and local Redis/API/worker runtime.

**Fields**:
- `SUPABASE_URL`: development project URL.
- `SUPABASE_ANON_KEY`: anon key for backend JWT-related configuration where
  needed.
- `SUPABASE_SERVICE_ROLE_KEY`: backend/worker-only service credential.
- `SUPABASE_JWT_SECRET`: backend token verification secret.
- `SUPABASE_VIDEO_BUCKET`: expected value `videos`.
- `SUPABASE_STORAGE_BUCKET`: expected value `violations`.
- `NEXT_PUBLIC_SUPABASE_URL`: frontend-safe project URL.
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`: frontend-safe publishable/anon key.
- `NEXT_PUBLIC_API_BASE_URL`: local API base URL.
- `REDIS_URL`: Redis connection string used by API/worker.

**Validation rules**:
- Real values live only in untracked `.env` files or environment variables.
- `.env.example` contains empty values or placeholders only.
- Frontend-exposed variables must not contain service-role credentials.

## Schema Setup Sequence

**Purpose**: Ordered Supabase SQL modules for local development setup.

**Fields**:
- `01_profiles.sql`: creates `profiles` table and owner read policy.
- `02_videos.sql`: creates `videos` table and owner/admin read policy.
- `03_violations.sql`: creates `violations` table and owner/admin read policy.
- `04_indexes.sql`: planned indexes for query and dashboard access paths.
- `05_realtime.sql`: planned realtime publication enablement for violations.

**Validation rules**:
- Files run in numeric order.
- Additive changes use `if not exists` where practical.
- Destructive changes require explicit migration and rollback documentation.

## Storage Bucket Configuration

**Purpose**: Supabase Storage setup for uploads and evidence crops.

**Fields**:
- `videos`: private bucket for original uploaded videos.
- `violations`: public-read bucket for violation evidence crops.

**Validation rules**:
- Upload smoke test stores original video objects in `videos`.
- Evidence crop URLs can be public only from `violations`.
- Bucket setup documentation must state how to verify visibility.

## Local Runtime Runbook

**Purpose**: Commands and expected results proving local infrastructure wiring.

**Fields**:
- `compose_command`: `docker compose up --build`.
- `health_check`: `GET http://localhost:8000/health`.
- `upload_check`: authenticated upload creates a video row and `videos` object.
- `worker_check`: worker service/process is running.

**Validation rules**:
- Health, upload, storage/row verification, and worker readiness complete in
  under 10 minutes after environment values are available.
- Smoke test does not require full ML inference.

## Deployment Artifact Set

**Purpose**: Reviewable production deployment artifacts for infrastructure
owners.

**Fields**:
- `docs/supabase-setup.md`
- `docs/devops-smoke-test.md`
- `k8s/README.md`
- `k8s/namespace.yaml`
- `k8s/redis.yaml`
- `k8s/api.yaml`
- `k8s/worker.yaml`
- `k8s/frontend.yaml`
- `k8s/secrets.example.yaml`
- `k8s/kustomization.yaml`
- `.github/workflows/deploy.yml`
- `.github/deploy.yml`: existing empty/nonstandard file, not the target
  workflow path.

**Validation rules**:
- Manifests use placeholder image names and secret references.
- CI/CD outline covers build, push, deploy, and validation stages.
- Actual rollout, DNS, TLS, and environment-specific provisioning are out of
  scope.
- `k8s/` is created by this feature; it is not an existing directory.
- Terraform, Helm, ArgoCD, and External Secrets are not required dependencies.

## Secret Reference

**Purpose**: Non-secret pointer to a required credential.

**Fields**:
- `name`: stable environment variable or secret key name.
- `scope`: local, CI, or cluster.
- `provider`: untracked `.env`, workload identity, GCP Secret Manager, or
  documented Kubernetes Secret placeholder.
- `consumer`: frontend, API, worker, CI, or Kubernetes workload.

**Validation rules**:
- No tracked file contains real secret values.
- Service-role credentials are only consumed by API and worker contexts.
- CI uses workload identity where available.
- External Secrets operator is not required.
