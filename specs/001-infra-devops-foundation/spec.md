# Feature Specification: Infrastructure and DevOps Foundation

**Feature Branch**: `001-infra-devops-foundation`

**Created**: 2026-06-29

**Status**: Draft

**Input**: User description: "Create the Infrastructure and DevOps foundation for the existing Helmet Violation Detection monorepo. The feature lets team developers configure a Supabase development project, run the database schema in the correct order, create required storage buckets, enable auth and realtime behavior for violations, run Redis/API/worker locally with Docker Compose, and follow smoke-test instructions that prove the backend health endpoint and Supabase-backed upload path are wired correctly. It also provides production deployment artifacts for the infrastructure owner: Kubernetes manifests for FastAPI API, Celery worker, Redis, optional frontend, and a GitHub Actions deployment pipeline outline for GKE using Artifact Registry and secret management. The feature must protect secrets, avoid committed .env files, and work with the current repository structure instead of creating a new application."

## Clarifications

### Session 2026-06-29

- Q: What storage bucket access policy should the infrastructure foundation document? → A: `videos` bucket private; `violations` bucket public-read for evidence crops.
- Q: What must the local smoke test prove for the infrastructure foundation? → A: Health endpoint passes; authenticated upload creates a video record and object in `videos`; worker process is running.
- Q: Which components may use Supabase anon/publishable keys versus service-role credentials? → A: Frontend uses anon/publishable key for auth/session only; API and worker use service-role key for storage and database writes.
- Q: What is the production deployment boundary for this feature? → A: Provide Kubernetes manifests and GitHub Actions deploy outline only; no actual production deployment execution.
- Q: What secret handling model should local, CI, and cluster environments use? → A: Local secrets in untracked `.env`; CI uses workload identity; cluster uses GCP Secret Manager references or documented Kubernetes Secret placeholders.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure Development Infrastructure (Priority: P1)

A team developer can configure a development Supabase project, apply the
project schema in the documented order, create the required storage buckets,
and enable the authentication and realtime behavior needed for violation
workflows without exposing secrets in the repository.

**Why this priority**: The application cannot support uploads, violation
evidence, authentication, or realtime dashboards until the shared development
backend is reproducible.

**Independent Test**: A developer follows the documented setup from a clean
checkout using placeholder examples, applies schema steps in order, creates the
required buckets, and verifies that no real secret values were added to tracked
files.

**Acceptance Scenarios**:

1. **Given** a clean checkout and access to an empty development backend project,
   **When** the developer follows the setup guide, **Then** profiles, videos,
   violations, storage buckets, auth settings, and realtime behavior are ready
   for local development.
2. **Given** a developer has real project credentials, **When** they configure
   local environment files, **Then** the credentials remain local-only and the
   repository contains only placeholders or examples.

---

### User Story 2 - Run and Smoke Test Local Runtime (Priority: P2)

A team developer can start the local Redis, API, and worker runtime and follow
smoke-test instructions that prove both the backend health endpoint and the
Supabase-backed upload path are wired correctly.

**Why this priority**: Local runtime validation is the first deployment gate and
must work before production deployment artifacts are trusted.

**Independent Test**: A developer starts the documented local runtime, runs the
smoke-test checklist, confirms the health check passes, submits an authenticated
small upload, verifies a video record and private `videos` object exist, and
confirms the worker process is running.

**Acceptance Scenarios**:

1. **Given** local configuration is complete, **When** the developer starts the
   runtime, **Then** Redis, API, and worker services are running and observable.
2. **Given** the runtime is running, **When** the developer performs the smoke
   tests, **Then** the health endpoint passes and the upload path reaches the
   configured development backend without credential leakage.
3. **Given** a smoke test fails, **When** the developer reads the runbook,
   **Then** the likely configuration, service, or backend setup issue is clear
   enough to troubleshoot without inspecting source code.

---

### User Story 3 - Prepare Production Deployment Artifacts (Priority: P3)

An infrastructure owner can review production deployment artifacts for the API,
worker, Redis, optional frontend, and deployment pipeline outline, with secret
management clearly separated from source-controlled manifests. The feature
provides reviewable artifacts and an outline only, not an actual production
rollout.

**Why this priority**: Production deployment planning is required, but it must
follow the proven local path and must not introduce hardcoded credentials.

**Independent Test**: The infrastructure owner reviews the manifests and
pipeline outline, verifies that each runtime component is represented, confirms
that image inputs are placeholders and secret inputs use GCP Secret Manager
references or documented Kubernetes Secret placeholders, and checks that the
deployment documentation explains how to provide secrets outside the repository.

**Acceptance Scenarios**:

1. **Given** the local runtime has been validated, **When** the infrastructure
   owner reviews production artifacts, **Then** API, worker, Redis, and optional
   frontend deployment needs are represented in the current repository.
2. **Given** deployment credentials are required, **When** the owner follows the
   deployment guide, **Then** secrets are created or referenced outside source
   control and no manifest contains real secret material.
3. **Given** image publishing and deployment automation are needed, **When** the
   owner reviews the pipeline outline, **Then** the expected build, publish, and
   deploy stages are documented with required inputs and validation gates.

### Edge Cases

- A developer runs schema files out of order; the guide must make the required
  order obvious and the smoke tests must reveal missing dependencies.
- Required storage buckets already exist; setup must document whether to reuse
  them and how to verify their access policy.
- Realtime publication for violations is disabled or incomplete; the setup must
  include a verification step for dashboard updates.
- Local runtime starts before environment variables are configured; smoke tests
  must fail with actionable configuration guidance.
- Upload smoke test succeeds in storing the original file but fails to enqueue
  processing; the runbook must distinguish storage wiring from worker wiring.
- Production deployment artifacts are reviewed without access to real secrets;
  placeholders and secret creation steps must still make the deployment inputs
  clear.
- Optional frontend deployment is excluded; production artifacts must still make
  API, worker, and Redis deployment complete.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST provide a development setup guide for creating or
  configuring the required backend development project used by the monorepo.
- **FR-002**: The setup guide MUST list schema files in the exact order they must
  be applied and state how to verify that each required data area is present.
- **FR-003**: The feature MUST document required storage buckets for original
  videos and violation evidence, with the `videos` bucket private and the
  `violations` bucket public-read for evidence crops in development.
- **FR-004**: The feature MUST document authentication setup required for team
  development accounts and role-aware access behavior.
- **FR-005**: The feature MUST document realtime behavior needed for violation
  updates and include a verification step for it.
- **FR-006**: The feature MUST provide local runtime instructions that start
  Redis, the backend API, and the background worker together.
- **FR-007**: The feature MUST include a smoke-test checklist that verifies the
  backend health endpoint from a developer workstation.
- **FR-008**: The feature MUST include a smoke-test checklist that verifies the
  health endpoint passes, an authenticated upload creates a video record and
  object in the private `videos` bucket, and the worker process is running.
- **FR-009**: The feature MUST document that frontend configuration uses only
  anon or publishable credentials for authentication and session behavior, while
  API and worker services use service-role credentials for storage and database
  writes through untracked local `.env`, GCP Secret Manager references, or
  documented Kubernetes Secret placeholders.
- **FR-010**: The feature MUST document how developers supply required local
  environment values through untracked `.env` files without committing real
  environment files.
- **FR-011**: The feature MUST provide production deployment artifacts for the
  backend API, background worker, Redis, and optional frontend as reviewable
  manifests and a deployment outline only.
- **FR-012**: The feature MUST include a deployment pipeline outline that covers
  build, publish, deploy, and validation stages, but MUST NOT require actual
  production deployment execution, DNS setup, TLS setup, or environment-specific
  provisioning.
- **FR-013**: Production deployment documentation MUST identify all required
  secret inputs and explain that CI uses workload identity while cluster
  workloads consume GCP Secret Manager references or documented Kubernetes
  Secret placeholders.
- **FR-014**: The feature MUST keep all generated artifacts inside the current
  monorepo structure and MUST NOT create a new application or parallel monorepo.
- **FR-015**: The feature MUST include review guidance that allows a reviewer to
  confirm no real secrets, tokens, service keys, kubeconfigs, certificates,
  private keys, or real environment files are tracked.
- **FR-016**: The feature MUST document a local-first promotion rule: production
  deployment artifacts are not considered ready until local Redis, API, and
  worker smoke tests pass.

### Constitution Alignment *(mandatory when applicable)*

- **CA-001**: Real secrets stay out of the repository; only placeholder values,
  example names, GCP Secret Manager references, or documented Kubernetes Secret
  placeholders may be tracked.
- **CA-002**: Infrastructure changes include local run commands and smoke tests
  for Redis, API, worker, backend health, and the upload path.
- **CA-003**: Frontend-facing configuration uses publishable or anonymous
  backend access values, while trusted backend services use privileged service
  credentials only through untracked local `.env`, GCP Secret Manager
  references, or documented Kubernetes Secret placeholders.
- **CA-004**: Schema setup documents a clear execution order and avoids
  destructive data changes unless a migration and rollback plan is included.
- **CA-005**: Deployment and CI/CD artifacts use workload identity, GCP Secret
  Manager references, or documented Kubernetes Secret placeholders, never
  hardcoded secret values.
- **CA-006**: All artifacts extend the existing repository layout and do not
  scaffold a new project.

### Key Entities *(include if feature involves data)*

- **Development Environment Configuration**: The set of local-only values,
  placeholders, and documented inputs required for developers to connect the
  monorepo to a development backend project. Frontend values are limited to
  anon or publishable credentials for auth/session behavior; API and worker
  values include service-role credentials for trusted storage and database
  writes.
- **Schema Setup Sequence**: The ordered list of database schema steps and
  verification checks required before the application can store profiles,
  videos, and violations.
- **Storage Bucket Configuration**: The expected buckets, purpose, visibility,
  and validation checks for original videos and violation evidence. Original
  uploads are stored in a private `videos` bucket; violation evidence crops are
  stored in a public-read `violations` bucket.
- **Local Runtime Runbook**: The developer-facing instructions and smoke-test
  results proving the local API, worker, and upload path are running. The smoke
  test covers API health, authenticated upload storage and video record creation,
  and worker process readiness; it does not require full model inference.
- **Deployment Artifact Set**: The production-facing manifests and pipeline
  outline covering runtime components, image inputs, secret inputs, and
  validation gates. The artifact set is reviewable and non-executing by default;
  actual rollout, DNS, TLS, and environment provisioning are outside this
  feature.
- **Secret Reference**: A documented placeholder or approved non-secret
  reference that identifies a required credential without storing the credential
  value. Local references point to untracked `.env` values, CI references use
  workload identity, and cluster references point to GCP Secret Manager
  references or documented Kubernetes Secret placeholders. External Secrets is
  not required.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new team developer can complete development backend setup and
  local configuration from a clean checkout in under 45 minutes using the
  documented guide.
- **SC-002**: 100% of required schema steps, storage buckets, auth behavior, and
  realtime behavior have an explicit verification step.
- **SC-003**: A developer can start the local runtime and complete health,
  authenticated upload, storage-record verification, and worker readiness smoke
  tests in under 10 minutes after environment values are available.
- **SC-004**: Reviewers can identify every required production secret input and
  its approved provisioning path, including CI workload identity and cluster GCP
  Secret Manager references or documented Kubernetes Secret placeholders,
  without finding any real secret value in tracked files.
- **SC-005**: The production artifact review identifies deployment coverage for
  API, worker, Redis, optional frontend, build/publish/deploy stages, a
  post-deploy validation gate, and confirms no production rollout execution is
  required by this feature.
- **SC-006**: All generated files are located in the existing repository areas
  reserved for documentation, deployment, workflow, or service configuration.
- **SC-007**: At least 90% of team developers following the runbook report that
  setup and smoke-test steps are clear enough to complete without maintainer
  assistance.

## Assumptions

- The existing monorepo remains the system of record for backend, frontend,
  model, documentation, and deployment artifacts.
- Team developers have permission to create or configure a development backend
  project and obtain local-only credentials from the project owner.
- Local credentials are stored only in untracked `.env` files.
- CI can use workload identity for cloud access, and cluster deployments can
  reference GCP Secret Manager entries or documented Kubernetes Secret
  placeholders. External Secrets is not required.
- The upload smoke test may use a small sample video or documented test file and
  only needs to prove storage and queue wiring, not full model accuracy.
- Production deployment artifacts are reviewable outlines and manifests, while
  actual rollout execution, DNS, TLS, production credentials, project IDs, and
  environment-specific values are outside this feature and supplied outside
  source control.
- Optional frontend deployment means the deployment artifacts document how to
  include it, while API, worker, and Redis remain mandatory.
