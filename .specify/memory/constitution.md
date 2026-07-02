<!--
SYNC IMPACT REPORT
- Version change: [CONSTITUTION_VERSION] -> 1.0.0
- List of modified principles:
  - [PRINCIPLE_1_NAME] -> I. Code Quality & Interface Standardization
  - [PRINCIPLE_2_NAME] -> II. Comprehensive Testing Discipline
  - [PRINCIPLE_3_NAME] -> III. Responsive UI/UX and Live Feedback Loop
  - [PRINCIPLE_4_NAME] -> IV. Performance Optimization & Resource Efficiency
  - [PRINCIPLE_5_NAME] -> V. Rigorous Data Governance & Observability
- Added sections:
  - Development & Architectural Constraints (renamed [SECTION_2_NAME])
  - Compliance & Quality Gates (renamed [SECTION_3_NAME])
- Removed sections: None
- Templates requiring updates (✅ updated / ⚠ pending):
  - .specify/templates/plan-template.md (✅ updated)
  - .specify/templates/spec-template.md (✅ updated)
  - .specify/templates/tasks-template.md (✅ updated)
- Follow-up TODOs: None
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

### V. Rigorous Data Governance & Observability
Compliance, safety audit, and system debugging require robust data storage and logging:
- For every detected violation, the system MUST crop the corresponding region of interest (the motorcyclist without a helmet) and save it as a high-fidelity image crop in Supabase `violations` storage bucket.
- Violation details, including the model used, tracking ID, and timestamp, MUST be written transactionally to the database.
- Structured logging is mandatory for both backend APIs and background workers. Every stage of the video processing pipeline MUST log structured telemetry, enabling rapid debugging of processing failures.

## Development & Architectural Constraints
The core stack is locked to prevent architectural fragmentation:
- **Frontend**: Next.js (React) for operator and admin interfaces.
- **Backend**: FastAPI for REST APIs and WebSockets.
- **Task Queue**: Celery with Redis for asynchronous video processing.
- **ML Engine**: ONNX Runtime and OpenCV for standard model evaluation.
- **Database & Storage**: Supabase (Postgres, Realtime, Auth, Storage).
- All deployments must support local orchestration via Docker Compose before cloud staging.

## Compliance & Quality Gates
Before code is merged to main:
1. All lint and format checks must pass.
2. Test suite coverage must not regress.
3. Integration and regression tests for all three supported models (YOLO, RT-DETR, Faster R-CNN) must pass using standard ONNX test weights.
4. Performance metrics (FPS, CPU/GPU utilization, and memory usage) must be recorded and compared against baseline metrics.

## Governance
- The Constitution is the supreme authority for development practices. Deviation from the principles outlined here requires a written justification in the Implementation Plan under "Complexity Tracking".
- Weekly audits will check the consistency of model predictions and database storage bucket cleaning procedures.
- Amendments to this constitution must be proposed via PR, approved by both the Lead ML Engineer and Product Owner, and increment the constitution version.
- Use `AGENTS.md` for runtime development guidance.

**Version**: 1.0.0 | **Ratified**: 2026-07-02 | **Last Amended**: 2026-07-02
