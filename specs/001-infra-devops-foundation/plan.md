# Implementation Plan: Infrastructure and DevOps Foundation

**Branch**: `001-infra-devops-foundation` | **Date**: 2026-06-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-infra-devops-foundation/spec.md`

## Summary

Build the infrastructure foundation for the existing Helmet Violation Detection
monorepo. The implementation will document Supabase development setup, add
missing ordered schema modules for indexes and realtime support, document
storage bucket policies, keep Docker Compose as the first local validation path,
add reviewable GKE deployment artifacts under `k8s/`, outline GitHub Actions
deployment through Artifact Registry at `.github/workflows/deploy.yml`, and
update runbooks with PowerShell-ready smoke tests. Infrastructure handoff docs
will be split across `docs/supabase-setup.md`, `docs/devops-smoke-test.md`, and
`k8s/README.md`. This feature does not implement ML inference, model
processing, or new frontend workflows.

## Technical Context

**Language/Version**: Python 3.13-compatible backend project managed by `uv`;
TypeScript/Next.js frontend exists but frontend deployment is optional for this
feature; SQL for Supabase schema modules; YAML for Compose, Kubernetes, and
GitHub Actions.

**Primary Dependencies**: FastAPI, Celery, Redis, Supabase, Docker Compose,
Docker images, Kubernetes manifests for GKE, Artifact Registry, GitHub Actions,
GCP Secret Manager or documented Kubernetes Secret placeholders. Terraform,
Helm, ArgoCD, and External Secrets are not required dependencies.

**Storage**: Supabase Postgres tables `profiles`, `videos`, `violations`;
Supabase Storage bucket `videos` private; Supabase Storage bucket `violations`
public-read for evidence crops; Redis for local queue/broker state.

**Testing**: PowerShell-friendly smoke tests using `docker compose ps`,
`Invoke-RestMethod` for `GET /health`, authenticated upload to
`POST /videos/upload`, Supabase verification for video row and private storage
object, and worker process readiness checks.

**Target Platform**: Local developer workstation via existing
`docker-compose.yml`; production deployment artifacts target GKE on GCP with
images published to Artifact Registry. Actual production rollout, DNS, TLS, and
environment provisioning are out of scope.

**Project Type**: Existing web application monorepo with `backend/`,
`frontend/`, `models/`, `crawl/`, `docs/`, `.github/`, and `.specify/`.
The `k8s/` directory does not exist yet and will be created by this feature.

**Performance Goals**: Developer can complete local runtime smoke tests in
under 10 minutes after environment values are available. New developer setup
guide supports development backend setup in under 45 minutes.

**Constraints**: No real secrets, service-role keys, tokens, kubeconfigs,
certificates, private keys, or real `.env` files may be committed. Frontend uses
anon/publishable keys only for auth/session. API and worker use service-role
credentials only from local untracked env, GCP Secret Manager references, or
documented Kubernetes Secret placeholders. Schema changes must be ordered and
non-destructive where practical. Do not introduce Terraform, Helm, ArgoCD, or
External Secrets as required dependencies.

**Scale/Scope**: Single infrastructure feature for the current monorepo.
Mandatory scope includes Supabase setup docs, ordered schema additions, local
Compose smoke tests, k8s manifests for API/worker/Redis/optional frontend, and a
GitHub Actions deployment outline at `.github/workflows/deploy.yml`.
Existing `.github/deploy.yml` is currently empty/nonstandard and is not the
target workflow path. Excludes ML inference implementation and frontend workflow
implementation.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Secret Hygiene**: PASS. Plan uses placeholders, untracked local `.env`,
  workload identity, GCP Secret Manager references, or documented Kubernetes
  Secret placeholders only.
- **Infrastructure Runbook**: PASS. Quickstart will define local run command and
  smoke tests for Redis, API, worker, health, and upload path.
- **Local-First Runtime**: PASS. Existing Docker Compose remains the first
  validation path before any GKE artifact review.
- **Supabase Least Privilege**: PASS. Frontend only uses anon/publishable keys;
  API and worker use service-role credentials from non-committed sources.
- **Schema Safety**: PASS. Existing numeric schema order is preserved and new
  schema modules will be appended for indexes/realtime with idempotent SQL where
  practical.
- **Deployment Secrets**: PASS. GKE and CI/CD artifacts will use workload
  identity, GCP Secret Manager references, or documented Kubernetes Secret
  placeholders, never hardcoded values.
- **Repository Fit**: PASS. Artifacts extend `backend/supabase/schema/`, `docs/`,
  `.github/`, `k8s/`, and the current spec directory only.

## Project Structure

### Documentation (this feature)

```text
specs/001-infra-devops-foundation/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- deployment-artifacts.md
|   |-- local-smoke-tests.md
|   `-- supabase-setup.md
`-- tasks.md
```

### Source Code (repository root)

```text
backend/
|-- Dockerfile.api
|-- Dockerfile.worker
|-- app/
`-- supabase/
    `-- schema/
        |-- 01_profiles.sql
        |-- 02_videos.sql
        |-- 03_violations.sql
        |-- 04_indexes.sql
        `-- 05_realtime.sql

docs/
|-- supabase-setup.md
`-- devops-smoke-test.md

k8s/
|-- README.md
|-- namespace.yaml
|-- redis.yaml
|-- api.yaml
|-- worker.yaml
|-- frontend.yaml
|-- secrets.example.yaml
`-- kustomization.yaml

.github/
`-- workflows/
    `-- deploy.yml

.github/
`-- deploy.yml        # existing empty/nonstandard file; not used as target workflow

docker-compose.yml
.env.example
```

**Structure Decision**: Use the existing monorepo layout. Supabase schema
additions stay under `backend/supabase/schema/`, runtime runbooks stay under
`docs/supabase-setup.md` and `docs/devops-smoke-test.md`, production manifests
and deployment handoff stay under a new `k8s/` directory with `k8s/README.md`,
and the CI/CD outline is placed under `.github/workflows/deploy.yml`.
The existing `.github/deploy.yml` is empty/nonstandard and will not be used as
the deployment workflow. No new application scaffold or parallel monorepo is
introduced.

## Complexity Tracking

No constitution violations or extra complexity exceptions are required.

## Phase 0: Research

See [research.md](research.md). All planning unknowns are resolved with concrete
decisions for Supabase schema ordering, storage policies, local smoke tests,
GKE artifact boundaries, and secret handling.

## Phase 1: Design

Design artifacts:

- [data-model.md](data-model.md)
- [contracts/supabase-setup.md](contracts/supabase-setup.md)
- [contracts/local-smoke-tests.md](contracts/local-smoke-tests.md)
- [contracts/deployment-artifacts.md](contracts/deployment-artifacts.md)
- [quickstart.md](quickstart.md)

## Constitution Check: Post-Design

- **Secret Hygiene**: PASS. Contracts and quickstart specify placeholders and
  untracked `.env` only; no real secrets are introduced.
- **Infrastructure Runbook**: PASS. Quickstart contains PowerShell-friendly
  local run and smoke-test commands.
- **Local-First Runtime**: PASS. Quickstart validates Compose before deployment
  artifact review.
- **Supabase Least Privilege**: PASS. Supabase contract fixes frontend versus
  backend credential ownership.
- **Schema Safety**: PASS. Data model and contracts require append-only ordered
  schema modules with idempotent operations where practical.
- **Deployment Secrets**: PASS. Deployment contract requires workload identity,
  GCP Secret Manager references, or documented Kubernetes Secret placeholders;
  Terraform, Helm, ArgoCD, and External Secrets are not required.
- **Repository Fit**: PASS. All artifacts target existing repository paths.
