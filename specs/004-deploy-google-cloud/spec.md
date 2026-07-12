# Feature Specification: Google Cloud Deployment

**Feature Branch**: `004-deploy-google-cloud`

**Created**: 2026-07-12

**Status**: Ready

**Input**: User description: "now, i want to deploy, the cloud i choose is google cloud"

## Clarifications

### Session 2026-07-12

- Q: Which Google Cloud deployment decisions are fixed before planning? → A: Use GKE Autopilot in asia-southeast1, Artifact Registry in asia-southeast1, one Traefik LoadBalancer, public Dashboard and Ingestion API, internal Auth/Orchestration/Notification/Inference Worker services, in-cluster Redis with a small PersistentVolumeClaim, external Supabase via Secret Manager, fixed replicas initially, GitHub Actions deployment on main, and budget alerts at 50%, 90%, and 100% of the $300 free-trial budget.
- Q: What manifest tooling should the deployment use? → A: Kustomize with base manifests and environment overlays.
- Q: What namespace strategy should the deployment use? → A: One GKE cluster with separate namespaces per environment.
- Q: What TLS and domain setup should the deployment use? → A: Use a DuckDNS free subdomain with Let's Encrypt TLS via cert-manager before demo or production use; a temporary LoadBalancer IP is acceptable only for early development smoke tests.
- Q: What resource request and limit strategy should the deployment use? → A: Start with a conservative per-service baseline and a larger CPU-only Inference Worker profile, then tune from smoke-test metrics.
- Q: What image tagging and rollback strategy should the deployment use? → A: Tag images with the commit SHA and roll back by redeploying the previous known-good SHA.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Access the System on Google Cloud (Priority: P1)

As a traffic operations user, I want the helmet violation detection system to be available from a Google Cloud-hosted environment so that I can log in, upload videos, monitor processing, and review violation results outside local development.

**Why this priority**: Cloud access is the core outcome of this feature. Without a reachable cloud environment, operators and reviewers cannot validate the system in a realistic deployment setting.

**Independent Test**: Can be fully tested by opening the cloud application URL, logging in with a test operator account, uploading a valid sample video, tracking the job until completion, and viewing the violation results page.

**Acceptance Scenarios**:

1. **Given** the Google Cloud deployment is marked ready for demo or production use, **When** an authorized user opens the application URL, **Then** the login page loads successfully through a DuckDNS subdomain over a valid Let's Encrypt TLS connection.
2. **Given** an authenticated operator, **When** they upload a supported traffic video, **Then** the upload is accepted, processing status is visible, and final violation results can be reviewed from the cloud environment.
3. **Given** an authenticated administrator, **When** they access operational dashboard views, **Then** they can inspect service status, recent processing activity, and violation trends from cloud-hosted data.
4. **Given** the deployment is ready, **When** users access the cloud system, **Then** only the Dashboard and Ingestion API are public-facing, while Auth, Orchestration, Notification, and Inference Worker remain internal-only.

---

### User Story 2 - Configure Cloud Environment Safely (Priority: P1)

As a project maintainer, I want all deployment configuration for Google Cloud to be explicit, repeatable, and separated from source code so that releases can be reproduced without exposing credentials or breaking service connections.

**Why this priority**: A cloud deployment is only useful if it can be repeated safely. Configuration mistakes can expose sensitive data, break uploads, or disconnect detection workers from required services.

**Independent Test**: Can be fully tested by preparing a fresh cloud environment using documented configuration values, deploying the system, and verifying that authentication, uploads, detection processing, storage, realtime updates, and reporting all work without manually editing source files.

**Acceptance Scenarios**:

1. **Given** a fresh Google Cloud environment, **When** required configuration values are supplied, **Then** the system starts with all required services connected and no secrets committed to the repository.
2. **Given** a missing or invalid required configuration value, **When** the deployment is checked, **Then** the release is blocked or clearly marked unhealthy with an actionable message.
3. **Given** separate staging and production configurations, **When** a release is promoted, **Then** each environment keeps its own credentials, storage locations, and externally visible URLs.
4. **Given** cloud secrets are required, **When** workloads start, **Then** they read approved secret values through a cloud-managed secret access path instead of repository files or hand-entered runtime values.

---

### User Story 3 - Monitor and Recover the Deployment (Priority: P2)

As an administrator, I want clear health, logging, alerting, and rollback signals for the Google Cloud deployment so that issues can be detected and resolved quickly during demos or operations.

**Why this priority**: The detection system includes live uploads, background processing, storage, and dashboards. Operators need confidence that failures are visible and recoverable.

**Independent Test**: Can be fully tested by forcing a non-destructive failure in a staging environment, confirming that the degraded service is visible in health/status views, checking that logs identify the failing area, and rolling back or restoring service within the defined recovery target.

**Acceptance Scenarios**:

1. **Given** one deployed service becomes unhealthy, **When** an administrator checks deployment health, **Then** the unhealthy area is identified without requiring direct access to user data.
2. **Given** a failed or degraded release, **When** rollback is initiated, **Then** the previous known-good version is restored and the application remains usable for authorized users.
3. **Given** a detection job fails in cloud processing, **When** an operator views the job status, **Then** the failure is visible with a user-friendly message and enough operational context for support to investigate.
4. **Given** changes are merged into the main branch, **When** the release workflow runs successfully, **Then** images are built, published to the regional registry, and deployed to the cloud environment with a visible release result.
5. **Given** a release is deployed, **When** maintainers inspect the running version, **Then** each service image can be traced back to the commit SHA that produced it.

---

### User Story 4 - Control Cost and Scale for Demos and Operations (Priority: P3)

As a project owner, I want the Google Cloud deployment to have clear capacity expectations and cost controls so that demos and ongoing experiments do not create unexpected bills or unstable performance.

**Why this priority**: Cost and scale controls are important for sustainable operation, but they follow the core need to make the system deployable and observable.

**Independent Test**: Can be fully tested by reviewing documented limits, running an agreed demo workload, confirming performance stays within target ranges, and verifying that usage alerts or caps are active.

**Acceptance Scenarios**:

1. **Given** a demo workload of sample videos and concurrent users, **When** the workload runs in Google Cloud, **Then** the system remains responsive and completes processing within expected limits.
2. **Given** cloud usage approaches the defined project budget or quota threshold, **When** monitoring evaluates usage, **Then** responsible maintainers receive a clear warning before costs exceed the agreed limit.
3. **Given** no active demo or processing workload, **When** the environment is idle, **Then** nonessential resource usage is minimized according to the agreed operating mode.
4. **Given** deployment has not yet started, **When** budget safeguards are reviewed, **Then** budget alerts exist at 50%, 90%, and 100% of the $300 free-trial budget.

### Edge Cases

- If the cloud application URL is reachable but a dependent service is unavailable, users receive a clear degraded-service message instead of a blank or misleading screen.
- If credentials, storage permissions, or external service settings are missing, deployment readiness checks fail before users attempt uploads or processing.
- If a large upload is interrupted during cloud use, the user sees whether it can be resumed or must be retried.
- If background processing exceeds expected duration, the job remains visible with a delayed status rather than disappearing from the tracker.
- If a newly promoted release fails basic smoke checks, the system can return to the previous known-good release.
- If budget or quota thresholds are reached, the environment protects the project from runaway usage while preserving evidence needed for troubleshooting.
- If an internal-only service is accidentally exposed publicly, release readiness checks fail until exposure matches the approved service boundary.
- If the inference workload requests too few resources for the selected model, the job fails visibly and does not hide worker restarts from operators or maintainers.
- If the DuckDNS record or TLS certificate is not ready, the environment may only be used for early development smoke tests through the temporary LoadBalancer IP and must not be treated as demo-ready.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a Google Cloud-hosted environment for the helmet violation detection application.
- **FR-002**: The cloud environment MUST use GKE Autopilot in the asia-southeast1 region as the initial runtime target.
- **FR-003**: Authorized users MUST be able to complete the core workflow in the cloud: log in, upload a supported video, track detection status, and review violation evidence.
- **FR-004**: The deployment MUST support separate staging and production-ready configuration profiles so releases can be validated before broader use.
- **FR-005**: All sensitive deployment values MUST be managed outside source code and must not appear in committed repository files, user-facing pages, or logs.
- **FR-006**: The deployment MUST store required external service credentials in GCP Secret Manager and grant workloads access through a GKE service account with the Secret Manager Secret Accessor role.
- **FR-007**: The cloud environment MUST connect the Next.js Dashboard, FastAPI services, Celery Inference Worker, Redis queue, Supabase Auth/Database/Storage/Realtime, and reporting features needed by existing application workflows.
- **FR-008**: The system MUST provide health visibility for the user-facing app, backend services, background processing, storage connectivity, and external dependencies required for detection workflows.
- **FR-009**: Administrators MUST be able to inspect deployment status, recent failures, and service health without exposing private credentials or unnecessary personal data.
- **FR-010**: The deployment MUST support rollback to a previous known-good release after a failed promotion or failed smoke check.
- **FR-011**: Cloud-hosted upload and processing workflows MUST preserve existing user-facing status transitions from queued or pending through processing to done or failed.
- **FR-012**: The deployment MUST preserve existing role-based access expectations for operators and administrators.
- **FR-013**: The deployment MUST preserve Vietnamese as the default user interface language and keep the existing English option available.
- **FR-014**: The deployment MUST include operational documentation covering release steps, required configuration, smoke checks, rollback, troubleshooting, and ownership contacts.
- **FR-015**: The project MUST continue to support local orchestration before cloud staging so that cloud deployment does not replace local verification workflows.
- **FR-016**: The Dashboard and Ingestion API MUST be the only public-facing application services in the initial cloud deployment.
- **FR-017**: Auth, Orchestration, Notification, and Inference Worker services MUST remain internal-only inside the cluster.
- **FR-018**: Redis MUST run in-cluster as a stateful service with a small persistent volume for the initial cost-controlled deployment.
- **FR-019**: Traefik MUST be the in-cluster ingress controller and MUST expose public traffic through a single cloud load balancer.
- **FR-020**: The initial deployment MUST use fixed replica counts of one or two pods per service and MUST defer autoscaling until traffic patterns are known.
- **FR-021**: GitHub Actions MUST build images, push them to Artifact Registry in asia-southeast1, and deploy to GKE after changes are merged to the main branch.
- **FR-022**: Budget alerts MUST be configured at 50%, 90%, and 100% of the $300 free-trial budget before the first cloud deployment.
- **FR-023**: Kubernetes deployment manifests MUST be organized with Kustomize base manifests and environment-specific overlays.
- **FR-024**: The initial deployment MUST use one GKE cluster with separate namespaces per environment to isolate staging and production configuration, access, and release state.
- **FR-025**: Demo-ready and production-ready access MUST use a DuckDNS free subdomain with Let's Encrypt TLS issued through cert-manager.
- **FR-026**: Temporary LoadBalancer IP access MUST be limited to early development smoke tests and MUST NOT be considered demo-ready.
- **FR-027**: API, Dashboard, Redis, Orchestration, and Notification workloads MUST start with conservative resource requests and limits appropriate for low-traffic smoke testing.
- **FR-028**: The Inference Worker MUST start with a larger CPU-only resource profile sized for ONNX Runtime and OpenCV processing, with GPU scheduling deferred out of scope for the initial deployment.
- **FR-029**: Resource requests and limits MUST be reviewed after smoke tests using observed CPU, memory, restart, and processing-duration metrics before any autoscaling work begins.
- **FR-030**: Container images MUST be tagged with the source commit SHA used to build them.
- **FR-031**: Rollback MUST redeploy the previous known-good commit SHA rather than relying on mutable image tags.
- **FR-032**: Release records MUST identify the commit SHA deployed for each service so maintainers can reproduce and audit cloud state.

### Key Entities

- **Cloud Environment**: A named Google Cloud-hosted runtime such as staging or production, with its own application URL, configuration profile, access rules, and operational status.
- **Release**: A versioned application build promoted to a cloud environment, with a release time, verification status, and rollback target.
- **Deployment Configuration**: Environment-specific values required for authentication, storage, processing, realtime updates, reporting, and public access.
- **Kustomize Overlay**: An environment-specific manifest layer that customizes shared deployment resources without duplicating the full base configuration.
- **Environment Namespace**: A Kubernetes namespace dedicated to one deployment environment, with its own workload configuration, secret bindings, release state, and access controls.
- **Public Endpoint**: The externally accessible URL for Dashboard and Ingestion API traffic, using DuckDNS and TLS for demo-ready or production-ready use.
- **GKE Workload**: A deployed service or worker in the cluster, with an exposure boundary, replica count, resource profile, service account, and health status.
- **Resource Profile**: The requested and maximum CPU and memory envelope assigned to a workload, with separate expectations for lightweight services and the inference worker.
- **Ingress Route**: A public routing rule managed through the shared ingress controller for Dashboard and Ingestion API traffic.
- **Service Health Record**: A status snapshot showing whether each required application area is healthy, degraded, or unavailable.
- **Operational Alert**: A warning or incident signal tied to availability, processing failures, quota, budget, or configuration risk.
- **Smoke Check Result**: A record of post-deployment validation covering login, upload, processing, results review, dashboard access, and administrative health checks.
- **Known-Good SHA**: The last commit SHA whose deployed images passed smoke checks and remain eligible as a rollback target.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can promote a validated release to the Google Cloud staging environment and complete smoke checks in under 30 minutes.
- **SC-002**: 95% of authorized users can open the cloud application login page in under 3 seconds during the agreed demo workload.
- **SC-003**: At least 90% of sample videos in the agreed smoke-test set complete the full upload-to-results workflow without manual intervention.
- **SC-004**: Administrators can identify whether the app, processing, storage, and external dependencies are healthy within 2 minutes of starting an operational check.
- **SC-005**: A failed release can be rolled back to the previous known-good version in under 10 minutes after the rollback decision is made.
- **SC-006**: No deployment secrets are found in committed files, user-facing pages, or routine application logs during release review.
- **SC-007**: Cost or quota warnings are visible to maintainers before the agreed monthly budget or quota threshold is exceeded.
- **SC-008**: The first cloud deployment uses no more than one public cloud load balancer for application traffic.
- **SC-009**: A main-branch release produces traceable container images and a visible deployment result without manual image publishing.
- **SC-010**: Before demo or production use, the public application endpoint presents a valid Let's Encrypt certificate for the configured DuckDNS subdomain.
- **SC-011**: During smoke tests, maintainers can review per-workload CPU, memory, restart count, and job processing duration before approving resource profile changes.
- **SC-012**: After any deployment, maintainers can identify the exact commit SHA running for every deployed service within 2 minutes.

## Assumptions

- Google Cloud is the selected cloud provider for this deployment feature.
- The first cloud deployment prioritizes low idle cost under the GCP free trial over high availability and automatic scale-out.
- The first production-ready target includes one staging environment and one production-ready configuration path.
- Existing authentication, upload, detection, storage, realtime notification, dashboard, and reporting workflows remain in scope.
- Model training is out of scope for this feature; the deployment uses already-prepared detection models and existing application behavior.
- Public internet access may be restricted to authorized users, but operators still need a stable application URL for demos or operations.
- Local verification remains required before cloud staging, consistent with the project constitution.
- Supabase remains an external managed service and is not migrated into Google Cloud as part of this feature.
- Memorystore is out of scope for the initial deployment because Redis will be self-hosted in the cluster to reduce cost.
- Horizontal autoscaling is out of scope for the initial deployment and will be revisited after traffic patterns are measured.
- GPU-backed inference is out of scope for the initial GKE Autopilot deployment.
