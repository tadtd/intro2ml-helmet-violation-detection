<!--
Sync Impact Report
Version change: 1.0.0 -> 1.1.0
Combined Principles from Infrastructure-DevOps and 001-detect-helmet-violations branches:
- Added principles:
  - I. Code Quality & Interface Standardization
  - II. Comprehensive Testing Discipline
  - III. Responsive UI/UX and Live Feedback Loop
  - IV. Performance Optimization & Resource Efficiency
  - V. Secret Hygiene Is Mandatory
  - VI. Supabase Least Privilege
  - VII. Kubernetes and CI/CD Secret Isolation
  - VIII. Local-First Runtime
  - IX. Infrastructure Changes Require Local Runbooks
  - X. Ordered, Non-Destructive Schema Changes
  - XI. Rigorous Data Governance & Observability
  - XII. Repository-Fit Artifacts
Added/Modified sections:
- Consolidated Development & Architectural Constraints
- Consolidated Compliance & Quality Gates
-->
# Helmet Violation Detection System Constitution

## Core Principles

### I. Code Quality & Interface Standardization
All code written in this project MUST be modular, statically typed, and structured. In particular:
- Every machine learning model wrapper MUST implement a standardized inference wrapper that conforms to the common `Detection` dataclass interface.
- No model-specific code or tensor formats should bleed into the API or Celery task layers. All bounding box logic and coordinates MUST use a uniform representation `(x1, y1, x2, y2)`.
- Python dependency and environment management MUST use `uv` exclusively. Frontend packages MUST be managed cleanly via `npm`.
- Code must be formatted with standard formatting tools (e.g., `black` or `ruff` for Python; `prettier` for Frontend/TypeScript).

### II. Comprehensive Testing Discipline
We enforce a strict testing workflow for all ML and system changes:
- Automated contract and integration tests MUST be executed and verified before pushing model wrapper or API modifications.
- Model prediction outputs, bounding box mappings, and class indexes (e.g., motorbike, helmet, non-helmet) MUST have regression tests verifying they parse ONNX outputs consistently.
- Integrations with external services (such as Supabase Auth, Storage, and Postgres Database) MUST use mock interfaces during unit and contract tests to prevent flaky test runs and API rate-limiting issues.

### III. Responsive UI/UX and Live Feedback Loop
The operator and admin dashboard must offer a seamless, real-time feedback experience:
- WebSocket video stream processing (such as `/ws/camera`) MUST minimize latency to under 100ms per frame to prevent operational lag.
- Interactive charts, realtime notification feeds, and lists of violations MUST subscribe to live Supabase Realtime updates.
- User video upload flows must provide clear, live status indicators transitioning dynamically through `pending` -> `processing` -> `done`/`failed` stages. No silent failures.

### IV. Performance Optimization & Resource Efficiency
Because this application runs heavy deep learning inference (ONNX Runtime, OpenCV) alongside WebSockets and database queries, system resource usage must be heavily optimized:
- Video decoding and frame-by-frame inference MUST run asynchronously in Celery background workers, ensuring the FastAPI HTTP thread pool never gets blocked.
- Memory usage in workers MUST be monitored to prevent memory leaks from OpenCV video capture or ONNX sessions. Large files should be cleaned up immediately from worker `/tmp/` storage after processing.
- Bounding box overlay and tracking computations MUST be optimized to run at target framerates (e.g., minimum 15-30 FPS depending on model architecture).

### V. Secret Hygiene Is Mandatory
Real secrets MUST NOT be committed. This includes tokens, service role keys, real `.env` files, kubeconfigs, certificates, private keys, and equivalent credentials. Only documented placeholders, examples, or local-only dummy values may be stored in the repository.

Rationale: the system integrates with Supabase, CI/CD, and deployment targets where a leaked credential can expose user data, storage objects, or production infrastructure.

### VI. Supabase Least Privilege
Frontend code MUST use only publishable or anon Supabase keys. Backend services, workers, migrations, and trusted administrative tooling MAY use the service role key only through environment variables or a secret manager. Service role keys MUST NOT appear in browser bundles, public config, or committed files.

Rationale: Supabase service role keys bypass Row Level Security and must remain server-side only.

### VII. Kubernetes and CI/CD Secret Isolation
Kubernetes manifests and CI/CD workflows MUST NOT hardcode secrets. They MUST use a documented secret manager integration or secret placeholders with documented commands or steps for creating the required secrets.

Rationale: deployment artifacts are often copied between environments, so secret material must stay outside the repository and outside static manifests.

### VIII. Local-First Runtime
Docker Compose MUST run Redis, the FastAPI API services, and the Celery workers successfully before Kubernetes deployment work is considered ready. Kubernetes manifests, cloud deployment, and CI/CD automation MUST build on the proven local Compose path.

Rationale: the API services, worker queue, and ML processing flow form the minimum runtime backbone. Debugging that backbone locally is required before adding cluster complexity.

### IX. Infrastructure Changes Require Local Runbooks
Every change to Docker Compose, Kubernetes, CI/CD, Supabase infrastructure, Redis, API services, workers, or related deployment configuration MUST document how to run it locally and how to perform a local smoke test.

Rationale: infrastructure that cannot be reproduced and checked locally is too risky for a course project with multiple moving parts.

### X. Ordered, Non-Destructive Schema Changes
Supabase schema files and migrations MUST have a clear execution order. Schema changes SHOULD be idempotent where practical and MUST avoid destructive changes to existing data unless a documented migration and rollback plan exists.

Rationale: violation evidence, video metadata, profiles, and audit-relevant rows must remain stable as the data model evolves.

### XI. Rigorous Data Governance & Observability
Compliance, safety audit, and system debugging require robust data storage and logging:
- For every detected violation, the system MUST crop the corresponding region of interest (the motorcyclist without a helmet) and save it as a high-fidelity image crop in Supabase `violations` storage bucket.
- Violation details, including the model used, tracking ID, and timestamp, MUST be written transactionally to the database.
- Structured logging is mandatory for both backend APIs and background workers. Every stage of the video processing pipeline MUST log structured telemetry, enabling rapid debugging of processing failures.

### XII. Repository-Fit Artifacts
Generated artifacts MUST fit the current repository structure. Work MUST extend the existing `backend/`, `frontend/`, `models/`, `crawl/`, `docs/`, `.specify/`, and deployment paths as appropriate, and MUST NOT create a new monorepo or parallel project scaffold for the same system.

Rationale: duplicating the project structure makes implementation, review, and deployment harder and risks diverging from the plan for this course project.

## Development & Architectural Constraints
The core stack is locked to prevent architectural fragmentation:
- **Frontend**: Next.js (React) for operator and admin interfaces.
- **Backend**: FastAPI for REST APIs and WebSockets.
- **Task Queue**: Celery with Redis for asynchronous video processing.
- **ML Engine**: ONNX Runtime and OpenCV for standard model evaluation.
- **Database & Storage**: Supabase (Postgres, Realtime, Auth, Storage).
- All deployments must support local orchestration via Docker Compose before cloud staging.
- `.env.example` files MAY contain empty values or documented placeholders only.
- Local setup documentation MUST identify required environment variables without embedding real secret values.
- Infrastructure documentation MUST include at least one smoke test that proves Redis, API gateway, microservices, and workers are reachable or running for local Compose changes.
- Supabase schema updates MUST state the intended order of execution.
- Kubernetes and CI/CD changes MUST document how required secrets are created or injected outside source control.

## Compliance & Quality Gates
Before code is merged to main:
1. All lint and format checks must pass.
2. Test suite coverage must not regress.
3. Integration and regression tests for all three supported models (YOLO, RT-DETR, Faster R-CNN) must pass using standard ONNX test weights.
4. Performance metrics (FPS, CPU/GPU utilization, and memory usage) must be recorded and compared against baseline metrics.
5. Reviews MUST reject changes that expose secrets, bypass Supabase least privilege, skip ordered migrations, or create a parallel repository structure.
6. Local Docker Compose validation is the required first deployment gate for Redis, API services, and worker changes.

## Governance
This constitution supersedes conflicting development practices for this repository. Amendments MUST be recorded in `.specify/memory/constitution.md`, include a Sync Impact Report, update affected templates or runtime guidance, and use semantic versioning.

Version policy:
- MAJOR: backward-incompatible governance changes or principle removals.
- MINOR: new principles, new required sections, or materially expanded guidance.
- PATCH: clarifications, wording fixes, or non-semantic refinements.

Compliance review is required for every feature plan, generated task list, and infrastructure-related change. If a change cannot satisfy a principle, the plan MUST document the violation, why it is necessary, and the simpler compliant alternative that was rejected.

**Version**: 1.1.0 | **Ratified**: 2026-07-07 | **Last Amended**: 2026-07-07
