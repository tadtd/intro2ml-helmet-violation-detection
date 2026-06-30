# Tasks: Infrastructure and DevOps Foundation

**Input**: Design documents from `specs/001-infra-devops-foundation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: No automated test tasks are required by the feature. Validation is documented through PowerShell-friendly smoke-test and review tasks.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks
- **[Story]**: Which user story the task belongs to, used only inside story phases
- Every task includes exact repository-relative file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare directories and baseline references used by all stories.

- [X] T001 Create missing feature target directories `docs/`, `k8s/`, and `.github/workflows/` while preserving existing `docs/README.md` and empty `.github/deploy.yml`
- [X] T002 [P] Review `.env.example` and document any placeholder-only environment variable gaps for Supabase, Redis, API, worker, and frontend-safe keys in `.env.example`
- [X] T003 [P] Review existing `docker-compose.yml` service names and ports for `redis`, `api`, and `worker` and record any mismatch against `specs/001-infra-devops-foundation/contracts/local-smoke-tests.md`
- [X] T004 [P] Review existing Supabase schema files `backend/supabase/schema/01_profiles.sql`, `backend/supabase/schema/02_videos.sql`, and `backend/supabase/schema/03_violations.sql` for ordered setup references needed by `docs/supabase-setup.md`
- [X] T005 [P] Review existing `.github/deploy.yml` and record that it is empty/nonstandard and not the target workflow for later documentation in `.github/workflows/deploy-gke.yml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared safety rules and artifact skeletons before user-story work begins.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006 Create skeleton `docs/supabase-setup.md` with sections for prerequisites, schema order, storage buckets, auth/realtime, verification, rollback/failure notes, and secret handling
- [X] T007 Create skeleton `docs/devops-smoke-test.md` with sections for prerequisites, local env safety, Compose startup, health check, authenticated upload check, Supabase verification, worker readiness, and troubleshooting
- [X] T008 Create skeleton `k8s/README.md` with sections for artifact purpose, non-goals, secret placeholders, image placeholders, review steps, and no Terraform/Helm/ArgoCD/External Secrets dependency
- [X] T009 Create placeholder-only Kubernetes directory manifest index `k8s/kustomization.yaml` with comments for planned resources; final resource references are completed in T038 after manifests exist
- [X] T010 Create GitHub Actions workflow skeleton `.github/workflows/deploy-gke.yml` with non-secret placeholders for GCP project, region, Artifact Registry, GKE cluster, workload identity, and a comment that `.github/deploy.yml` is empty/nonstandard and not the target workflow
- [X] T011 Document secret handling rules in `docs/devops-smoke-test.md` and `k8s/README.md`, covering untracked `.env`, workload identity, GCP Secret Manager references, Kubernetes Secret placeholders, and prohibited committed secret classes
- [X] T012 Verify no generated skeleton file contains real tokens, service-role keys, kubeconfigs, certificates, private keys, or real `.env` values in `docs/supabase-setup.md`, `docs/devops-smoke-test.md`, `k8s/README.md`, and `.github/workflows/deploy-gke.yml`

**Checkpoint**: Skeletons and safety constraints are ready for independently testable user-story implementation.

---

## Phase 3: User Story 1 - Configure Development Infrastructure (Priority: P1) MVP

**Goal**: A team developer can configure a Supabase development project, run schema files in order, create required storage buckets, enable auth/realtime behavior, and keep real secrets out of git.

**Independent Test**: From the documentation alone, a developer can follow setup steps for an empty Supabase development project, identify the ordered SQL files, create or verify buckets, and confirm only placeholders are tracked.

### Implementation for User Story 1

- [X] T013 [P] [US1] Add idempotent index migration `backend/supabase/schema/04_indexes.sql` for `videos.user_id`, `videos.created_at`, `violations.user_id`, `violations.video_id`, and `violations.timestamp`
- [X] T014 [P] [US1] Add realtime enablement migration `backend/supabase/schema/05_realtime.sql` for violation insert subscriptions using idempotent-safe SQL where practical
- [X] T015 [US1] Document exact schema execution order from `01_profiles.sql` through `05_realtime.sql` in `docs/supabase-setup.md`
- [X] T016 [US1] Document Supabase table verification expectations for `profiles`, `videos`, and `violations` with RLS enabled in `docs/supabase-setup.md`
- [X] T017 [US1] Document storage bucket policy decisions for private `videos` and public-read `violations` in `docs/supabase-setup.md`
- [X] T018 [US1] Document Supabase auth setup expectations for operator/admin team development accounts and role-aware access behavior in `docs/supabase-setup.md`
- [X] T019 [US1] Document realtime enablement and verification steps for violation inserts in `docs/supabase-setup.md`
- [X] T020 [US1] Document local-only Supabase credential ownership for frontend anon/publishable keys and API/worker service-role keys in `docs/supabase-setup.md`
- [X] T021 [US1] Add rollback and failure notes for out-of-order schema execution, existing buckets, missing RLS, and realtime setup failures in `docs/supabase-setup.md`
- [X] T022 [US1] Update `README.md` to link to `docs/supabase-setup.md` for detailed Supabase setup while preserving the concise root setup flow

**Checkpoint**: User Story 1 is complete when Supabase setup can be reviewed and followed independently without real secrets or unordered migration ambiguity.

---

## Phase 4: User Story 2 - Run and Smoke Test Local Runtime (Priority: P2)

**Goal**: A team developer can start Redis, API, and worker locally through Docker Compose and follow PowerShell-friendly smoke tests for health, authenticated upload, Supabase row/object verification, and worker readiness.

**Independent Test**: A developer can use `docs/devops-smoke-test.md` to start Compose, run the health command, run the authenticated upload command, inspect Supabase row/object results, and confirm the worker process is running without requiring ML inference.

### Implementation for User Story 2

- [X] T023 [P] [US2] Document PowerShell command to copy `.env.example` to untracked `.env` and list required local values in `docs/devops-smoke-test.md`
- [X] T024 [US2] Document `docker compose up --build` startup instructions and expected `docker compose ps` output for `redis`, `api`, and `worker` in `docs/devops-smoke-test.md`
- [X] T025 [US2] Document API health smoke test using `Invoke-RestMethod -Uri http://localhost:8000/health -Method Get` in `docs/devops-smoke-test.md`
- [X] T026 [US2] Document authenticated upload smoke test using `curl.exe` with `Authorization: Bearer <LOCAL_SUPABASE_USER_JWT>` and sample upload path `data/sample-smoke-small.mp4` in `docs/devops-smoke-test.md`
- [X] T027 [US2] Document Supabase verification steps for a `videos` row and matching private `videos` bucket object in `docs/devops-smoke-test.md`
- [X] T028 [US2] Document worker readiness checks using `docker compose ps worker` and `docker compose logs worker` in `docs/devops-smoke-test.md`
- [X] T029 [US2] Document troubleshooting for missing env values, API health failure, upload success without enqueue, missing storage object, and worker not running in `docs/devops-smoke-test.md`
- [X] T030 [US2] Explicitly document that local smoke tests do not require ML inference, violation crop generation, or frontend workflow validation in `docs/devops-smoke-test.md`
- [X] T031 [US2] Update `README.md` to link to `docs/devops-smoke-test.md` for detailed PowerShell smoke-test commands

**Checkpoint**: User Story 2 is complete when the local runbook proves Docker Compose health and upload wiring without relying on model inference or frontend workflows.

---

## Phase 5: User Story 3 - Prepare Production Deployment Artifacts (Priority: P3)

**Goal**: An infrastructure owner can review GKE Kubernetes manifests and a GitHub Actions deployment outline with secret management clearly separated from source-controlled files.

**Independent Test**: The infrastructure owner can inspect `k8s/` and `.github/workflows/deploy-gke.yml`, confirm all required runtime components are represented, see placeholder image/secret inputs, and verify no production rollout, DNS, TLS, Terraform, Helm, ArgoCD, or External Secrets dependency is required.

### Implementation for User Story 3

- [X] T032 [P] [US3] Create `k8s/namespace.yaml` with namespace metadata for the Helmet Violation Detection deployment placeholder
- [X] T033 [P] [US3] Create `k8s/redis.yaml` with Redis Deployment and Service placeholders for GKE review
- [X] T034 [P] [US3] Create `k8s/api.yaml` with FastAPI API Deployment and Service placeholders, image placeholder, container port, health path, and secret references
- [X] T035 [P] [US3] Create `k8s/worker.yaml` with Celery worker Deployment placeholder, image placeholder, command/args placeholder, and secret references
- [X] T036 [P] [US3] Create `k8s/frontend.yaml` with optional Next.js frontend Deployment and Service placeholders and comments marking it optional for this feature
- [X] T037 [P] [US3] Create `k8s/secrets.example.yaml` containing only placeholder secret names and instructions comments, with no secret values
- [X] T038 [US3] Finalize `k8s/kustomization.yaml` so it references every planned manifest file in `k8s/`
- [X] T039 [US3] Write `k8s/README.md` with GKE handoff notes, manifest review order, image placeholder replacement guidance, secret creation guidance, and out-of-scope boundaries for rollout, DNS, TLS, Terraform, Helm, ArgoCD, and External Secrets
- [X] T040 [US3] Create `.github/workflows/deploy-gke.yml` with reviewable stages for workload identity authentication, Docker image build, Artifact Registry push, GKE credential setup, manifest apply/render, and post-deploy health validation
- [X] T041 [US3] Add comments in `.github/workflows/deploy-gke.yml` identifying required placeholders for GCP project, workload identity provider, service account, Artifact Registry repository, image names, GKE cluster, namespace, and secret references
- [X] T042 [US3] Document in `k8s/README.md` that existing `.github/deploy.yml` is empty/nonstandard and `.github/workflows/deploy-gke.yml` is the target workflow path
- [X] T043 [US3] Review `k8s/*.yaml` and `.github/workflows/deploy-gke.yml` to ensure they contain placeholders only and no real project IDs, service-role keys, kubeconfigs, certificates, private keys, or secret values
- [X] T044 [US3] Update `README.md` to link to `k8s/README.md` and `.github/workflows/deploy-gke.yml` for deployment artifact review

**Checkpoint**: User Story 3 is complete when production deployment artifacts are reviewable, scoped to handoff, and free of real secrets.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Align docs, checklists, and generated artifacts across all stories.

- [X] T045 [P] Reconcile `specs/001-infra-devops-foundation/quickstart.md` with final `docs/supabase-setup.md`, `docs/devops-smoke-test.md`, `k8s/README.md`, and `.github/workflows/deploy-gke.yml`
- [X] T046 [P] Update `backend/README.md` to point Supabase schema and bucket setup readers to `docs/supabase-setup.md`
- [X] T047 [P] Review `specs/001-infra-devops-foundation/checklists/devops.md` and mark or note any requirement-quality gaps resolved by the final docs
- [X] T048 Validate task format and artifact scope in `specs/001-infra-devops-foundation/tasks.md`, ensuring every implementation task has a file path and no task introduces ML inference or frontend workflow implementation
- [X] T049 Run a repository secret-safety review over `.env.example`, `docs/`, `k8s/`, `.github/workflows/deploy-gke.yml`, and `README.md` to confirm only placeholders are tracked
- [X] T050 Run the documented local smoke-test commands from `docs/devops-smoke-test.md` if local Supabase credentials are available, otherwise record the credential blocker in `docs/devops-smoke-test.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 US1**: Depends on Phase 2. This is the MVP and should complete before US2 because smoke tests depend on Supabase setup guidance.
- **Phase 4 US2**: Depends on Phase 2 and benefits from US1 documentation for Supabase verification.
- **Phase 5 US3**: Depends on Phase 2. It can run in parallel with US1/US2 after skeletons exist, but final review should happen after US2 local-first validation docs are complete.
- **Phase 6 Polish**: Depends on desired user stories being complete.

### User Story Dependencies

- **US1 Configure Development Infrastructure**: Independent after Phase 2; MVP scope.
- **US2 Run and Smoke Test Local Runtime**: Independent after Phase 2, but uses US1 Supabase setup details for row/object verification.
- **US3 Prepare Production Deployment Artifacts**: Independent after Phase 2; must respect local-first boundary and should not require production rollout.

### Parallel Opportunities

- Setup reviews T002-T005 can run in parallel.
- Foundational skeletons T006-T010 can run in parallel before secret handling pass T011-T012.
- US1 migrations T013-T014 can run in parallel with documentation drafts T015-T020 after skeleton docs exist.
- US2 documentation tasks T023-T028 touch the same file and should be sequenced, while README link T031 can wait until the runbook content exists.
- US3 manifest tasks T032-T037 can run in parallel, then kustomization T038, README/workflow tasks T039-T042, and secret review T043.
- Polish tasks T045-T047 can run in parallel after stories complete; T048-T050 should run last.

---

## Parallel Examples

### User Story 1

```text
Task: "T013 [P] [US1] Add idempotent index migration backend/supabase/schema/04_indexes.sql"
Task: "T014 [P] [US1] Add realtime enablement migration backend/supabase/schema/05_realtime.sql"
```

### User Story 3

```text
Task: "T032 [P] [US3] Create k8s/namespace.yaml"
Task: "T033 [P] [US3] Create k8s/redis.yaml"
Task: "T034 [P] [US3] Create k8s/api.yaml"
Task: "T035 [P] [US3] Create k8s/worker.yaml"
Task: "T036 [P] [US3] Create k8s/frontend.yaml"
Task: "T037 [P] [US3] Create k8s/secrets.example.yaml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup and Phase 2 skeleton/safety tasks.
2. Complete Phase 3 User Story 1.
3. Stop and validate that Supabase setup, schema order, bucket policy, auth/realtime, rollback notes, and secret handling are documented.

### Incremental Delivery

1. Deliver US1 so team developers can configure Supabase safely.
2. Deliver US2 so team developers can run local Compose smoke tests.
3. Deliver US3 so infrastructure owners can review GKE and GitHub Actions handoff artifacts.
4. Run Phase 6 polish to align docs and secret-safety review.

### Team Parallel Strategy

After Phase 2, one developer can work on US1 schema/docs while another drafts US3 manifests. US2 should stay close to US1 because its smoke-test verification depends on the Supabase setup docs.

## Notes

- [P] tasks touch different files or can proceed without dependency on incomplete tasks.
- Story labels map to the three user stories in `specs/001-infra-devops-foundation/spec.md`.
- Do not add Terraform, Helm, ArgoCD, External Secrets, ML inference, or frontend workflow implementation tasks.
- Keep `.github/deploy.yml` documented as empty/nonstandard; create the target workflow at `.github/workflows/deploy-gke.yml`.
- Keep all secrets as placeholders, GCP Secret Manager references, Kubernetes Secret placeholder names, or untracked local `.env` values.

---

## Phase 7: Convergence

- [X] T051 Create the missing repository-local handoff directories `k8s/` and `.github/workflows/`, preserving existing `docs/README.md` and empty `.github/deploy.yml`, per FR-014 and SC-006 (partial)
- [X] T052 Add the reviewable GKE manifest set under `k8s/` for namespace, Redis, FastAPI API, Celery worker, optional frontend, secret placeholders, and final `k8s/kustomization.yaml` per FR-011 and US3 (missing)
- [X] T053 Add `.github/workflows/deploy-gke.yml` with placeholder-only workload identity, Artifact Registry build/push, GKE credential setup, manifest apply/render, and post-deploy health validation stages per FR-012 and US3 (missing)
- [X] T054 Document production secret inputs in `k8s/README.md`, `k8s/secrets.example.yaml`, and `.github/workflows/deploy-gke.yml` using workload identity, GCP Secret Manager references, or Kubernetes Secret placeholders per FR-013 and CA-005 (partial)
- [X] T055 Run a final production-artifact secret-safety review over `k8s/*.yaml`, `.github/workflows/deploy-gke.yml`, `.env.example`, `docs/`, and `README.md` to confirm only placeholders are tracked per FR-015 and SC-004 (partial)
- [X] T056 Reconcile `README.md`, `backend/README.md`, and `specs/001-infra-devops-foundation/quickstart.md` with the final Supabase, local smoke-test, Kubernetes, and workflow handoff docs per SC-005 and SC-007 (partial)
