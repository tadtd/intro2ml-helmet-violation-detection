# Feature Specification: Google Cloud Deployment

**Feature Branch**: `004-deploy-google-cloud`

**Created**: 2026-07-12

**Status**: Ready

**Input**: User description: "now, i want to deploy, the cloud i choose is google cloud"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Access the System on Google Cloud (Priority: P1)

As a traffic operations user, I want the helmet violation detection system to be available from a Google Cloud-hosted environment so that I can log in, upload videos, monitor processing, and review violation results outside local development.

**Why this priority**: Cloud access is the core outcome of this feature. Without a reachable cloud environment, operators and reviewers cannot validate the system in a realistic deployment setting.

**Independent Test**: Can be fully tested by opening the cloud application URL, logging in with a test operator account, uploading a valid sample video, tracking the job until completion, and viewing the violation results page.

**Acceptance Scenarios**:

1. **Given** the Google Cloud deployment is marked ready, **When** an authorized user opens the application URL, **Then** the login page loads successfully over a secure connection.
2. **Given** an authenticated operator, **When** they upload a supported traffic video, **Then** the upload is accepted, processing status is visible, and final violation results can be reviewed from the cloud environment.
3. **Given** an authenticated administrator, **When** they access operational dashboard views, **Then** they can inspect service status, recent processing activity, and violation trends from cloud-hosted data.

---

### User Story 2 - Configure Cloud Environment Safely (Priority: P1)

As a project maintainer, I want all deployment configuration for Google Cloud to be explicit, repeatable, and separated from source code so that releases can be reproduced without exposing credentials or breaking service connections.

**Why this priority**: A cloud deployment is only useful if it can be repeated safely. Configuration mistakes can expose sensitive data, break uploads, or disconnect detection workers from required services.

**Independent Test**: Can be fully tested by preparing a fresh cloud environment using documented configuration values, deploying the system, and verifying that authentication, uploads, detection processing, storage, realtime updates, and reporting all work without manually editing source files.

**Acceptance Scenarios**:

1. **Given** a fresh Google Cloud environment, **When** required configuration values are supplied, **Then** the system starts with all required services connected and no secrets committed to the repository.
2. **Given** a missing or invalid required configuration value, **When** the deployment is checked, **Then** the release is blocked or clearly marked unhealthy with an actionable message.
3. **Given** separate staging and production configurations, **When** a release is promoted, **Then** each environment keeps its own credentials, storage locations, and externally visible URLs.

---

### User Story 3 - Monitor and Recover the Deployment (Priority: P2)

As an administrator, I want clear health, logging, alerting, and rollback signals for the Google Cloud deployment so that issues can be detected and resolved quickly during demos or operations.

**Why this priority**: The detection system includes live uploads, background processing, storage, and dashboards. Operators need confidence that failures are visible and recoverable.

**Independent Test**: Can be fully tested by forcing a non-destructive failure in a staging environment, confirming that the degraded service is visible in health/status views, checking that logs identify the failing area, and rolling back or restoring service within the defined recovery target.

**Acceptance Scenarios**:

1. **Given** one deployed service becomes unhealthy, **When** an administrator checks deployment health, **Then** the unhealthy area is identified without requiring direct access to user data.
2. **Given** a failed or degraded release, **When** rollback is initiated, **Then** the previous known-good version is restored and the application remains usable for authorized users.
3. **Given** a detection job fails in cloud processing, **When** an operator views the job status, **Then** the failure is visible with a user-friendly message and enough operational context for support to investigate.

---

### User Story 4 - Control Cost and Scale for Demos and Operations (Priority: P3)

As a project owner, I want the Google Cloud deployment to have clear capacity expectations and cost controls so that demos and ongoing experiments do not create unexpected bills or unstable performance.

**Why this priority**: Cost and scale controls are important for sustainable operation, but they follow the core need to make the system deployable and observable.

**Independent Test**: Can be fully tested by reviewing documented limits, running an agreed demo workload, confirming performance stays within target ranges, and verifying that usage alerts or caps are active.

**Acceptance Scenarios**:

1. **Given** a demo workload of sample videos and concurrent users, **When** the workload runs in Google Cloud, **Then** the system remains responsive and completes processing within expected limits.
2. **Given** cloud usage approaches the defined project budget or quota threshold, **When** monitoring evaluates usage, **Then** responsible maintainers receive a clear warning before costs exceed the agreed limit.
3. **Given** no active demo or processing workload, **When** the environment is idle, **Then** nonessential resource usage is minimized according to the agreed operating mode.

### Edge Cases

- If the cloud application URL is reachable but a dependent service is unavailable, users receive a clear degraded-service message instead of a blank or misleading screen.
- If credentials, storage permissions, or external service settings are missing, deployment readiness checks fail before users attempt uploads or processing.
- If a large upload is interrupted during cloud use, the user sees whether it can be resumed or must be retried.
- If background processing exceeds expected duration, the job remains visible with a delayed status rather than disappearing from the tracker.
- If a newly promoted release fails basic smoke checks, the system can return to the previous known-good release.
- If budget or quota thresholds are reached, the environment protects the project from runaway usage while preserving evidence needed for troubleshooting.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a Google Cloud-hosted environment for the helmet violation detection application.
- **FR-002**: The cloud environment MUST expose the operator and administrator web experience through a secure, documented application entry point.
- **FR-003**: Authorized users MUST be able to complete the core workflow in the cloud: log in, upload a supported video, track detection status, and review violation evidence.
- **FR-004**: The deployment MUST support separate staging and production-ready configuration profiles so releases can be validated before broader use.
- **FR-005**: All sensitive deployment values MUST be managed outside source code and must not appear in committed repository files, user-facing pages, or logs.
- **FR-006**: The deployment MUST validate required configuration before or during release readiness checks and identify missing or invalid values with actionable messages.
- **FR-007**: The cloud environment MUST connect the web experience, authentication, storage, realtime updates, background processing, and reporting features needed by existing application workflows.
- **FR-008**: The system MUST provide health visibility for the user-facing app, backend services, background processing, storage connectivity, and external dependencies required for detection workflows.
- **FR-009**: Administrators MUST be able to inspect deployment status, recent failures, and service health without exposing private credentials or unnecessary personal data.
- **FR-010**: The deployment MUST support rollback to a previous known-good release after a failed promotion or failed smoke check.
- **FR-011**: Cloud-hosted upload and processing workflows MUST preserve existing user-facing status transitions from queued or pending through processing to done or failed.
- **FR-012**: The deployment MUST preserve existing role-based access expectations for operators and administrators.
- **FR-013**: The deployment MUST preserve Vietnamese as the default user interface language and keep the existing English option available.
- **FR-014**: The deployment MUST include operational documentation covering release steps, required configuration, smoke checks, rollback, troubleshooting, and ownership contacts.
- **FR-015**: The project MUST continue to support local orchestration before cloud staging so that cloud deployment does not replace local verification workflows.

### Key Entities

- **Cloud Environment**: A named Google Cloud-hosted runtime such as staging or production, with its own application URL, configuration profile, access rules, and operational status.
- **Release**: A versioned application build promoted to a cloud environment, with a release time, verification status, and rollback target.
- **Deployment Configuration**: Environment-specific values required for authentication, storage, processing, realtime updates, reporting, and public access.
- **Service Health Record**: A status snapshot showing whether each required application area is healthy, degraded, or unavailable.
- **Operational Alert**: A warning or incident signal tied to availability, processing failures, quota, budget, or configuration risk.
- **Smoke Check Result**: A record of post-deployment validation covering login, upload, processing, results review, dashboard access, and administrative health checks.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can promote a validated release to the Google Cloud staging environment and complete smoke checks in under 30 minutes.
- **SC-002**: 95% of authorized users can open the cloud application login page in under 3 seconds during the agreed demo workload.
- **SC-003**: At least 90% of sample videos in the agreed smoke-test set complete the full upload-to-results workflow without manual intervention.
- **SC-004**: Administrators can identify whether the app, processing, storage, and external dependencies are healthy within 2 minutes of starting an operational check.
- **SC-005**: A failed release can be rolled back to the previous known-good version in under 10 minutes after the rollback decision is made.
- **SC-006**: No deployment secrets are found in committed files, user-facing pages, or routine application logs during release review.
- **SC-007**: Cost or quota warnings are visible to maintainers before the agreed monthly budget or quota threshold is exceeded.

## Assumptions

- Google Cloud is the selected cloud provider for this deployment feature.
- The specific Google Cloud runtime choices will be finalized during planning while preserving the outcomes in this specification.
- The first production-ready target includes one staging environment and one production-ready configuration path.
- Existing authentication, upload, detection, storage, realtime notification, dashboard, and reporting workflows remain in scope.
- Model training is out of scope for this feature; the deployment uses already-prepared detection models and existing application behavior.
- Public internet access may be restricted to authorized users, but operators still need a stable application URL for demos or operations.
- Local verification remains required before cloud staging, consistent with the project constitution.
