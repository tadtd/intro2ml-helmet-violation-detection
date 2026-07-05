# Implementation Plan: Helmet Violation Detection System

**Branch**: `001-detect-helmet-violations` | **Date**: 2026-07-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from [specs/001-detect-helmet-violations/spec.md](file:///e:/hcmus/semester-6/intro2ml-helmet-violation-detection/specs/001-detect-helmet-violations/spec.md)

## Summary
Implement a high-performance, production-ready motorcycle helmet violation detection system. The backend follows a microservices architecture fronted by an API Gateway, communicating synchronously via gRPC (e.g., auth check) and asynchronously via Redis pub-sub/message queuing. Video processing runs asynchronously on Celery workers using a workload-split queue configuration (`default` for API operations, `inference` for model execution). Model inference uses ONNX Runtime to evaluate YOLO, RT-DETR, and Faster R-CNN weights. Raw outputs are processed using tracking velocity/displacement heuristics to filter stationary vehicles, and cropped using a composite bounding box union (motorbike + violating head) before saving metadata to Supabase and media to S3. The application will support localization defaulting to Vietnamese with a toggle option for English.

## Technical Context

**Language/Version**: Python 3.13 (Backend Services & Workers), Node.js v18 (Frontend/Next.js)

**Primary Dependencies**: FastAPI (REST/WS), gRPC/Protobuf (Sync communication), Celery (Task Queue), Redis (Event Broker & Celery Backend), ONNX Runtime (Inference Engine), OpenCV (Video processing & cropping), Next.js v14 (Frontend UI)

**Storage**: Supabase Postgres (schema-per-service design), S3-compatible Storage (bucket for uploaded videos and violation crops)

**Testing**: Pytest (unit, contract, and integration tests for services), Jest/React Testing Library (Frontend UI tests)

**Target Platform**: Google Kubernetes Engine (GKE) Standard with CPU and GPU (NVIDIA T4/L4) Node Pools

**Project Type**: Microservices Web Application & Distributed Inference Pipeline

**Performance Goals**: 
* Live monitoring frame rate of at least 15 FPS.
* Live feed round-trip frame overlay latency under 100ms.
* API query response time for 10k violation records under 2 seconds.

**Constraints**:
* No model retraining (rely on raw output heuristics).
* Conserve GCP credits: cluster and GPU node pools must scale to zero or be deleted/scaled down when idle.
* Row-Level Security (RLS) on database tables.

**Scale/Scope**: 
* Monorepo containing Next.js frontend, `backend/` directory housing Traefik API Gateway and 6 FastAPI microservices, and GKE/K8s configuration.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Constraint | Status | Notes |
|------------------------|--------|-------|
| I. Code Quality & Interface Standardization | ✅ PASS | All backend model wrappers implement `OnnxDetectionModel` and return a unified `Detection` dataclass. Bounding boxes strictly use `(x1, y1, x2, y2)`. |
| II. Comprehensive Testing Discipline | ✅ PASS | Pytest suite covers unit, contract, and integration logic. Supabase and S3 calls will be fully mocked in tests. |
| III. Responsive UI/UX and Live Feedback Loop | ✅ PASS | WebSockets stream frames with <100ms latency. Video status indications map dynamically to status table fields. |
| IV. Performance Optimization & Resource Efficiency | ✅ PASS | Inference is decoupled into background Celery workers. OpenCV and ONNX capture handles will explicitly release resources and clean up `/tmp/` files. |
| V. Rigorous Data Governance & Observability | ✅ PASS | Image crops save the composite union of motorbike and violating head. Telemetry is outputted via structured JSON logging. |
| Core Stack & Local Orchestration | ✅ PASS | Stack is locked to Next.js, FastAPI, Celery, Redis, ONNX, OpenCV, Supabase, and S3. Supported locally via `docker-compose.yml`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-detect-helmet-violations/
├── plan.md              # This file
├── research.md          # Microservices design, event patterns, and GKE scaling options
├── data-model.md        # Database schema per service
├── quickstart.md        # Docker Compose local quickstart and testing guide
└── contracts/           # API and gRPC interface schemas
    ├── api-gateway/     # Route mapping configuration
    ├── auth/            # auth.proto for gRPC
    └── events/          # Event schemas for Redis (video_uploaded, violation_detected)
```

### Source Code (repository root layout)

```text
backend/
├── api-gateway/         # API Gateway (Traefik or custom FastAPI Gateway)
├── auth-service/        # Auth service API
├── ingestion-service/   # Video upload and stream ingestion API
├── orchestration-service/ # Celery task dispatcher and lifecycle manager
├── inference-service/   # Celery worker performing ONNX inference
├── notification-service/ # In-app, push, and i18n formatter
└── dashboard-service/   # Query API for operators/admins (RLS-enabled)
frontend/                # Next.js Application
docker-compose.yml       # Local monorepo run configuration
k8s/                     # Kubernetes manifests & Helm charts
```

**Structure Decision**: Microservices layout with dedicated directories per service to support separate Docker builds, multi-stage compilation, and containerization.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Microservices Architecture | Separation of heavy GPU-based inference workloads from standard CPU-bound I/O tasks. | Monolithic design would result in GPU node waste and API blocking during video uploads. |
| Hybrid Communication (gRPC + Redis) | Synchronous auth verification requires low latency (gRPC), while high-throughput pipeline events must be non-blocking (Redis event-driven model). | Direct HTTP REST for all inter-service communication creates tight coupling and propagation delays. |
