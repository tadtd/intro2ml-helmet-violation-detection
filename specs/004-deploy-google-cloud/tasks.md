# Tasks: Google Cloud Deployment

**Input**: Design documents from `specs/004-deploy-google-cloud/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: This feature uses validation and smoke-check tasks rather than TDD-only test tasks. Existing backend/frontend tests remain required by CI.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently after the shared foundation is ready.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks
- **[Story]**: User story label, used only inside user story phases
- Every task includes an exact target file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the deployment workspace and baseline documentation without changing application behavior.

- [x] T001 Create deployment directory structure in `deploy/k8s/base/`, `deploy/k8s/overlays/staging/`, `deploy/k8s/overlays/production/`, and `deploy/scripts/win/`
- [x] T002 [P] Create deployment overview and ownership notes in `docs/deployment/google-cloud.md`
- [x] T003 [P] Create environment variable inventory from `.env.example` in `docs/deployment/environment-inventory.md`
- [x] T004 [P] Create Artifact Registry image naming reference in `docs/deployment/artifact-registry.md`
- [x] T005 [P] Create initial GitHub Actions workflow skeleton in `.github/workflows/deploy-gke.yml`
- [x] T006 [P] Create Kustomize root placeholder in `deploy/k8s/base/kustomization.yaml`
- [x] T007 [P] Create staging overlay placeholder in `deploy/k8s/overlays/staging/kustomization.yaml`
- [x] T008 [P] Create production overlay placeholder in `deploy/k8s/overlays/production/kustomization.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared manifest conventions, service accounts, image names, namespace layout, and local validation helpers required by all user stories.

**Critical**: No user story work should begin until this phase is complete.

- [x] T009 Define common Kubernetes labels and annotations in `deploy/k8s/base/common-labels.yaml`
- [x] T010 Create base namespace resources for `helmet-staging` and `helmet-production` in `deploy/k8s/base/namespace/namespaces.yaml`
- [x] T011 Create base Kubernetes service accounts for frontend, APIs, workers, Redis, Traefik, and cert-manager in `deploy/k8s/base/serviceaccounts/serviceaccounts.yaml`
- [x] T012 Create shared ConfigMap for non-secret runtime settings in `deploy/k8s/base/config/runtime-config.yaml`
- [x] T013 Create placeholder Secret Manager reference manifests without plaintext values in `deploy/k8s/base/secrets/secret-refs.yaml`
- [x] T014 Create base image transformer file for commit-SHA image replacement in `deploy/k8s/base/images.yaml`
- [x] T015 Create staging namespace patch in `deploy/k8s/overlays/staging/namespace.yaml`
- [x] T016 Create production namespace patch in `deploy/k8s/overlays/production/namespace.yaml`
- [x] T017 Create staging environment README with required manual values in `deploy/k8s/overlays/staging/README.md`
- [x] T018 Create production environment README with required manual values in `deploy/k8s/overlays/production/README.md`
- [x] T019 Create manifest render validation script in `deploy/scripts/win/validate-manifests.ps1`
- [x] T020 Create deployment prerequisites checklist in `docs/deployment/prerequisites.md`
- [x] T021 Update `.gitignore` to ignore local deployment scratch files and generated release-state files in `.gitignore`

**Checkpoint**: Foundation ready; user story implementation can start in priority order or in parallel by area.

---

## Phase 3: User Story 1 - Access the System on Google Cloud (Priority: P1) MVP

**Goal**: Authorized users can reach the cloud-hosted system through the approved public endpoint, log in, upload a video, track processing, and review results.

**Independent Test**: Open the DuckDNS HTTPS URL, log in with a test operator, upload a sample video, observe job status, view results, and confirm only approved public services are exposed.

### Implementation for User Story 1

- [x] T022 [P] [US1] Create frontend Deployment manifest in `deploy/k8s/base/workloads/frontend-deployment.yaml`
- [x] T023 [P] [US1] Create frontend Service manifest in `deploy/k8s/base/services/frontend-service.yaml`
- [x] T024 [P] [US1] Create ingestion Deployment manifest in `deploy/k8s/base/workloads/ingestion-deployment.yaml`
- [x] T025 [P] [US1] Create ingestion Service manifest in `deploy/k8s/base/services/ingestion-service.yaml`
- [x] T026 [P] [US1] Create dashboard API Deployment manifest in `deploy/k8s/base/workloads/dashboard-deployment.yaml`
- [x] T027 [P] [US1] Create dashboard API Service manifest in `deploy/k8s/base/services/dashboard-service.yaml`
- [x] T028 [P] [US1] Create notification Deployment manifest in `deploy/k8s/base/workloads/notification-deployment.yaml`
- [x] T029 [P] [US1] Create notification Service manifest in `deploy/k8s/base/services/notification-service.yaml`
- [x] T030 [P] [US1] Create realtime stream Deployment manifest in `deploy/k8s/base/workloads/realtime-stream-deployment.yaml`
- [x] T031 [P] [US1] Create realtime stream Service manifest in `deploy/k8s/base/services/realtime-stream-service.yaml`
- [x] T032 [US1] Create Traefik Deployment manifest in `deploy/k8s/base/traefik/traefik-deployment.yaml`
- [x] T033 [US1] Create single Traefik LoadBalancer Service manifest in `deploy/k8s/base/traefik/traefik-service.yaml`
- [x] T034 [US1] Create Traefik ingress class and route provider configuration in `deploy/k8s/base/traefik/traefik-config.yaml`
- [x] T035 [US1] Create public route manifests for `/`, `/api/v1/videos`, `/api/v1/violations`, `/ws/status`, and `/ws/camera` in `deploy/k8s/base/traefik/ingress-routes.yaml`
- [x] T036 [US1] Create cert-manager ClusterIssuer or Issuer template for Let's Encrypt HTTP-01 in `deploy/k8s/base/cert-manager/issuer.yaml`
- [x] T037 [US1] Create certificate manifest for the DuckDNS host in `deploy/k8s/base/cert-manager/certificate.yaml`
- [x] T038 [US1] Add staging host and TLS patches in `deploy/k8s/overlays/staging/patches/public-endpoint.yaml`
- [x] T039 [US1] Add production host and TLS patches in `deploy/k8s/overlays/production/patches/public-endpoint.yaml`
- [x] T040 [US1] Create service exposure validation script in `deploy/scripts/win/validate-exposure.ps1`
- [x] T041 [US1] Create cloud smoke test script for login page, upload route, result route, and WebSocket reachability in `deploy/scripts/win/smoke-test.ps1`
- [x] T042 [US1] Document DuckDNS early smoke-test and demo-ready endpoint flow in `docs/deployment/public-endpoint.md`

**Checkpoint**: User Story 1 is independently testable as the MVP cloud access path.

---

## Phase 4: User Story 2 - Configure Cloud Environment Safely (Priority: P1)

**Goal**: A maintainer can configure staging and production-ready environments repeatably without committing secrets or manually editing source code.

**Independent Test**: Prepare a fresh environment using documented values, render/apply overlays, verify workloads consume approved secrets, and confirm no plaintext secrets appear in manifests or logs.

### Implementation for User Story 2

- [x] T043 [P] [US2] Create Secret Manager setup script for required helmet secrets in `deploy/scripts/win/create-secret-manager-secrets.ps1`
- [x] T044 [P] [US2] Create Workload Identity Federation binding script for Kubernetes service accounts in `deploy/scripts/win/configure-workload-identity.ps1`
- [x] T045 [P] [US2] Document required GitHub Actions variables and secrets in `docs/deployment/github-actions-secrets.md`
- [x] T046 [US2] Create External Secrets or SecretProviderClass manifest for Supabase and DuckDNS references in `deploy/k8s/base/secrets/secret-provider.yaml`
- [x] T047 [US2] Patch staging Secret Manager project and secret references in `deploy/k8s/overlays/staging/patches/secrets.yaml`
- [x] T048 [US2] Patch production Secret Manager project and secret references in `deploy/k8s/overlays/production/patches/secrets.yaml`
- [x] T049 [US2] Create auth Deployment manifest with internal-only exposure in `deploy/k8s/base/workloads/auth-deployment.yaml`
- [x] T050 [US2] Create auth ClusterIP Service manifest in `deploy/k8s/base/services/auth-service.yaml`
- [x] T051 [US2] Create orchestration Deployment manifest with internal-only exposure in `deploy/k8s/base/workloads/orchestration-deployment.yaml`
- [x] T052 [US2] Create orchestration ClusterIP Service manifest in `deploy/k8s/base/services/orchestration-service.yaml`
- [x] T053 [US2] Create inference worker Deployment manifest with internal-only worker settings in `deploy/k8s/base/workloads/inference-worker-deployment.yaml`
- [x] T054 [US2] Create Redis StatefulSet manifest with append-only persistence in `deploy/k8s/base/redis/redis-statefulset.yaml`
- [x] T055 [US2] Create Redis ClusterIP Service manifest in `deploy/k8s/base/redis/redis-service.yaml`
- [x] T056 [US2] Create Redis PersistentVolumeClaim template in `deploy/k8s/base/redis/redis-pvc.yaml`
- [x] T057 [US2] Create plaintext secret scan script for manifests and workflow logs in `deploy/scripts/win/scan-secrets.ps1`
- [x] T058 [US2] Document environment setup and secret rotation procedure in `docs/deployment/secret-management.md`

**Checkpoint**: User Story 2 is independently testable as a safe, repeatable configuration path.

---

## Phase 5: User Story 3 - Monitor and Recover the Deployment (Priority: P2)

**Goal**: Maintainers can deploy from GitHub Actions, inspect health, identify the running commit SHA, and roll back to the previous known-good SHA.

**Independent Test**: Trigger a main-branch or manual deployment, verify commit-SHA images in GKE, force a non-destructive failure, inspect health/logs, and run rollback to a previous known-good SHA within the recovery target.

### Implementation for User Story 3

- [x] T059 [P] [US3] Add frontend lint/build job to `.github/workflows/deploy-gke.yml`
- [x] T060 [P] [US3] Add backend uv/pytest job to `.github/workflows/deploy-gke.yml`
- [x] T061 [US3] Add Google Cloud authentication via Workload Identity Federation to `.github/workflows/deploy-gke.yml`
- [x] T062 [US3] Add Docker Buildx build matrix for frontend and backend service images to `.github/workflows/deploy-gke.yml`
- [x] T063 [US3] Add Artifact Registry push step using commit-SHA tags to `.github/workflows/deploy-gke.yml`
- [x] T064 [US3] Add Kustomize image replacement and staging apply steps to `.github/workflows/deploy-gke.yml`
- [x] T065 [US3] Add rollout status checks for frontend, ingestion, auth, dashboard, notification, orchestration, inference-worker, realtime-stream, Redis, and Traefik to `.github/workflows/deploy-gke.yml`
- [x] T066 [US3] Add smoke-test workflow step invoking `deploy/scripts/win/smoke-test.ps1` in `.github/workflows/deploy-gke.yml`
- [x] T067 [US3] Add release-state artifact capture for deployed service SHAs in `.github/workflows/deploy-gke.yml`
- [x] T068 [P] [US3] Create release-state schema documentation in `docs/deployment/release-state.md`
- [x] T069 [P] [US3] Create rollback script that redeploys a previous known-good SHA in `deploy/scripts/win/rollback.ps1`
- [x] T070 [US3] Add manual workflow dispatch inputs for deploy, rollback, and smoke-test operations in `.github/workflows/deploy-gke.yml`
- [x] T071 [US3] Create health inspection script for pod status, events, logs, and image SHAs in `deploy/scripts/win/inspect-health.ps1`
- [x] T072 [US3] Document rollback and incident handling procedure in `docs/deployment/rollback-and-recovery.md`

**Checkpoint**: User Story 3 is independently testable as an observable deploy and rollback path.

---

## Phase 6: User Story 4 - Control Cost and Scale for Demos and Operations (Priority: P3)

**Goal**: Maintainers can confirm budget safeguards, predictable fixed replicas, resource profiles, and post-smoke-test tuning signals before demo use.

**Independent Test**: Review budget alerts, run a demo workload, confirm one public LoadBalancer, inspect resource metrics, and verify no autoscaling or GPU resources are enabled initially.

### Implementation for User Story 4

- [x] T073 [P] [US4] Create budget alert setup guide for 50%, 90%, and 100% thresholds in `docs/deployment/budget-alerts.md`
- [x] T074 [P] [US4] Create budget alert verification script wrapper in `deploy/scripts/win/validate-budget-alerts.ps1`
- [x] T075 [P] [US4] Create base resource profile patches for light API workloads in `deploy/k8s/base/resources/light-api-resources.yaml`
- [x] T076 [P] [US4] Create base resource profile patch for frontend in `deploy/k8s/base/resources/frontend-resources.yaml`
- [x] T077 [P] [US4] Create base resource profile patch for Redis in `deploy/k8s/base/resources/redis-resources.yaml`
- [x] T078 [P] [US4] Create base resource profile patch for Traefik in `deploy/k8s/base/resources/traefik-resources.yaml`
- [x] T079 [US4] Create larger CPU-only inference worker resource profile in `deploy/k8s/base/resources/inference-cpu-resources.yaml`
- [x] T080 [US4] Wire resource profile patches into `deploy/k8s/base/kustomization.yaml`
- [x] T081 [US4] Patch staging fixed replica counts in `deploy/k8s/overlays/staging/patches/replicas.yaml`
- [x] T082 [US4] Patch production fixed replica counts in `deploy/k8s/overlays/production/patches/replicas.yaml`
- [x] T083 [US4] Create metrics collection script for CPU, memory, restarts, and processing duration in `deploy/scripts/win/collect-smoke-metrics.ps1`
- [x] T084 [US4] Create cost and scale review checklist in `docs/deployment/cost-and-scale-review.md`
- [x] T085 [US4] Add validation that HPA and GPU resources are absent from initial manifests in `deploy/scripts/win/validate-manifests.ps1`

**Checkpoint**: User Story 4 is independently testable as the cost-control and scaling guardrail.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation cleanup, and consistency checks across all stories.

- [x] T086 [P] Update `specs/004-deploy-google-cloud/quickstart.md` with final script names and expected command outputs
- [x] T087 [P] Update `README.md` with a pointer to `docs/deployment/google-cloud.md`
- [x] T088 [P] Update `docs/deployment/google-cloud.md` with the final implementation order and owner checklist
- [x] T089 Run manifest rendering validation for staging and production using `deploy/scripts/win/validate-manifests.ps1`
- [x] T090 Run exposure validation using `deploy/scripts/win/validate-exposure.ps1`
- [x] T091 Run secret scan validation using `deploy/scripts/win/scan-secrets.ps1`
- [x] T092 Run local Docker Compose baseline validation using `docker-compose.yml`
- [x] T093 Run backend pytest validation from `backend/pyproject.toml`
- [x] T094 Run frontend lint and build validation from `frontend/package.json`
- [x] T095 Review all generated deployment documentation for consistency with `specs/004-deploy-google-cloud/contracts/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **US1 Access System (Phase 3)**: Depends on Foundational; MVP target.
- **US2 Safe Configuration (Phase 4)**: Depends on Foundational; can run alongside US1 if service manifest ownership is coordinated.
- **US3 Monitor and Recover (Phase 5)**: Depends on Foundational; CI/CD deploy steps become fully testable after US1 and US2 manifests exist.
- **US4 Cost and Scale (Phase 6)**: Depends on Foundational; resource patches can run alongside US1/US2 but final validation depends on complete manifests.
- **Polish (Phase 7)**: Depends on all selected stories.

### User Story Dependencies

- **User Story 1 (P1)**: MVP cloud access path; can start after Phase 2.
- **User Story 2 (P1)**: Safe configuration path; can start after Phase 2 and complements US1.
- **User Story 3 (P2)**: Deploy/observe/rollback path; depends on usable manifests from US1 and US2 for end-to-end workflow validation.
- **User Story 4 (P3)**: Cost and scale guardrails; depends on workload manifests but can create docs/scripts in parallel.

### Within Each User Story

- Manifests before overlay patches.
- Services before routes.
- Secret references before workload secret consumption.
- Workflow validation before deployment.
- Smoke checks before marking a SHA as known-good.

## Parallel Opportunities

- Setup docs and directory scaffolding tasks T002-T008 can run in parallel after T001.
- Foundational tasks T009-T021 touch separate files and can mostly run in parallel.
- US1 workload manifests T022-T031 can run in parallel before Traefik routes T032-T035.
- US2 scripts/docs T043-T045 can run in parallel with secret/workload manifests T046-T056.
- US3 validation scripts/docs T068-T069 and T071-T072 can run in parallel with workflow edits T059-T067.
- US4 resource profile files T073-T078 can run in parallel before kustomization wiring T080.

## Parallel Example: User Story 1

```text
Task: "T022 [P] [US1] Create frontend Deployment manifest in deploy/k8s/base/workloads/frontend-deployment.yaml"
Task: "T024 [P] [US1] Create ingestion Deployment manifest in deploy/k8s/base/workloads/ingestion-deployment.yaml"
Task: "T026 [P] [US1] Create dashboard API Deployment manifest in deploy/k8s/base/workloads/dashboard-deployment.yaml"
Task: "T028 [P] [US1] Create notification Deployment manifest in deploy/k8s/base/workloads/notification-deployment.yaml"
Task: "T030 [P] [US1] Create realtime stream Deployment manifest in deploy/k8s/base/workloads/realtime-stream-deployment.yaml"
```

## Parallel Example: User Story 2

```text
Task: "T043 [P] [US2] Create Secret Manager setup script for required helmet secrets in deploy/scripts/win/create-secret-manager-secrets.ps1"
Task: "T044 [P] [US2] Create Workload Identity Federation binding script for Kubernetes service accounts in deploy/scripts/win/configure-workload-identity.ps1"
Task: "T045 [P] [US2] Document required GitHub Actions variables and secrets in docs/deployment/github-actions-secrets.md"
```

## Parallel Example: User Story 3

```text
Task: "T059 [P] [US3] Add frontend lint/build job to .github/workflows/deploy-gke.yml"
Task: "T060 [P] [US3] Add backend uv/pytest job to .github/workflows/deploy-gke.yml"
Task: "T069 [P] [US3] Create rollback script that redeploys a previous known-good SHA in deploy/scripts/win/rollback.ps1"
Task: "T071 [US3] Create health inspection script for pod status, events, logs, and image SHAs in deploy/scripts/win/inspect-health.ps1"
```

## Parallel Example: User Story 4

```text
Task: "T073 [P] [US4] Create budget alert setup guide for 50%, 90%, and 100% thresholds in docs/deployment/budget-alerts.md"
Task: "T075 [P] [US4] Create base resource profile patches for light API workloads in deploy/k8s/base/resources/light-api-resources.yaml"
Task: "T076 [P] [US4] Create base resource profile patch for frontend in deploy/k8s/base/resources/frontend-resources.yaml"
Task: "T077 [P] [US4] Create base resource profile patch for Redis in deploy/k8s/base/resources/redis-resources.yaml"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundation.
3. Complete Phase 3 User Story 1.
4. Validate public access, TLS, approved routes, and upload/result flow.
5. Stop and demo the MVP before adding release automation or cost refinements.

### Incremental Delivery

1. Setup and foundation create shared manifest structure.
2. US1 delivers the reachable cloud application.
3. US2 makes environment configuration safe and repeatable.
4. US3 adds CI/CD, health inspection, and rollback.
5. US4 adds cost guardrails and resource tuning workflow.
6. Polish validates all scripts, docs, manifests, and local checks.

### Parallel Team Strategy

1. One person owns shared Kustomize structure and base conventions.
2. One person owns public access, Traefik, and TLS.
3. One person owns secrets, service accounts, and internal workloads.
4. One person owns CI/CD, smoke tests, rollback, and cost scripts.

## Notes

- `[P]` tasks are intended for different files and can be done concurrently after their phase prerequisites are met.
- `[US1]` through `[US4]` map directly to the user stories in `spec.md`.
- Do not commit plaintext secrets or generated credentials.
- Keep image tags immutable and commit-SHA based.
- Stop at each checkpoint to validate the story independently.
