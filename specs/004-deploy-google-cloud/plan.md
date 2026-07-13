# Implementation Plan: Google Cloud Deployment

**Branch**: `004-deploy-google-cloud` | **Date**: 2026-07-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-deploy-google-cloud/spec.md`

## Summary

Deploy the helmet violation detection system to Google Cloud using a cost-controlled GKE Autopilot cluster in `asia-southeast1`. The implementation will add Kubernetes manifests managed with Kustomize, one namespace per environment, Traefik as the single public ingress point, cert-manager-issued Let's Encrypt TLS for a DuckDNS subdomain, GCP Secret Manager access through Workload Identity Federation for GKE, in-cluster Redis with a small persistent volume, and GitHub Actions CI/CD that builds commit-SHA-tagged images, pushes them to Artifact Registry, deploys to GKE, and supports rollback by redeploying the previous known-good SHA.

## Technical Context

**Language/Version**: Python >=3.13 for FastAPI/Celery services managed with `uv`; TypeScript 5.x, Node.js v18+ for the Next.js frontend; YAML for Kubernetes, Kustomize, GitHub Actions, Traefik, and cert-manager resources.

**Primary Dependencies**: GKE Autopilot, Artifact Registry, GCP Secret Manager, Workload Identity Federation for GKE, Google Cloud Billing budgets/alerts, GitHub Actions, Docker Buildx, Kustomize, kubectl, Traefik v3.x, cert-manager, Let's Encrypt, DuckDNS, Redis 7 Alpine, Supabase, FastAPI, Celery, ONNX Runtime, OpenCV, Next.js 16, React 19.

**Storage**: External Supabase Postgres/Auth/Storage/Realtime; GCP Secret Manager for deployment secrets; Artifact Registry for container images; Redis StatefulSet with a small PersistentVolumeClaim for the initial in-cluster queue/cache; Kubernetes Secrets projected from Secret Manager or synchronized at deploy time; no Memorystore in the initial deployment.

**Testing**: Existing backend pytest suites per service; frontend `npm run lint` and `npm run build`; `docker compose` local smoke validation; `kubectl kustomize` or `kustomize build` manifest validation; GKE smoke checks for login, upload, processing, results, health, TLS, budget alerts, and rollback.

**Target Platform**: Google Kubernetes Engine Autopilot, region `asia-southeast1`, one cluster with environment namespaces, public access only through Traefik LoadBalancer and DuckDNS/Let's Encrypt for demo or production readiness.

**Project Type**: Containerized web application and backend microservice system.

**Performance Goals**: Cloud login page loads in under 3 seconds for 95% of authorized demo users; maintainers can identify service health within 2 minutes; rollback completes within 10 minutes; resource tuning uses observed CPU, memory, restart count, and processing duration from smoke tests; existing frontend overlay and UI responsiveness goals remain unchanged.

**Constraints**: $300 GCP free-trial budget with 50%/90%/100% alerts before deployment; one public cloud load balancer; no HPA initially; no GPU initially; commit-SHA image tags only for deployable releases; Dashboard and Ingestion API are public-facing, Auth/Orchestration/Notification/Inference Worker are internal-only; local Docker Compose verification remains required before cloud staging.

**Scale/Scope**: Initial low-traffic demo/staging deployment with fixed replicas: 1 replica for most workloads, optionally 2 replicas for public-facing Dashboard/Ingestion after smoke tests; CPU-only inference worker; one staging namespace and one production-ready namespace path; autoscaling and managed Redis deferred.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Constraint | Status | Notes |
|------------------------|--------|-------|
| I. Code Quality & Interface Standardization | PASS | Plan preserves Python `uv`, frontend `npm`, existing Dockerfiles, and typed service boundaries. Kustomize overlays avoid duplicating manifest logic across environments. |
| II. Comprehensive Testing Discipline | PASS | Plan requires existing pytest suites, frontend build/lint, local Compose smoke checks, manifest rendering checks, and GKE smoke/rollback validation before demo readiness. |
| III. Responsive UI/UX and Live Feedback Loop | PASS | Deployment preserves public Dashboard/Ingestion and realtime Notification/stream routing through Traefik while keeping existing status transitions visible. |
| IV. Performance Optimization & Resource Efficiency | PASS | GKE Autopilot, fixed replicas, one LoadBalancer, in-cluster Redis, CPU-only inference, and post-smoke-test resource tuning directly support free-trial cost control. |
| V. Rigorous Data Governance & Observability | PASS | Secret Manager, Workload Identity Federation, no committed secrets, health checks, release records, smoke results, and budget alerts are required. |
| Core Stack & Local Orchestration | PASS | Existing Next.js, FastAPI, Celery, Redis, ONNX Runtime, OpenCV, and Supabase stack is preserved; local Docker Compose validation remains required before cloud deployment. |

**Post-Design Re-check**: PASS. Phase 1 artifacts preserve all gates and add no constitution violations.

## Project Structure

### Documentation (this feature)

```text
specs/004-deploy-google-cloud/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── deployment-contract.md
│   ├── manifest-contract.md
│   └── cicd-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── auth/
├── common/
├── dashboard/
├── inference/
├── ingestion/
├── notification/
├── orchestration/
└── api-gateway/

frontend/
├── app/
├── components/
├── hooks/
├── messages/
├── services/
├── store/
└── Dockerfile

supabase/
├── migrations/
└── tests/

deploy/
├── k8s/
│   ├── base/
│   │   ├── namespace/
│   │   ├── workloads/
│   │   ├── services/
│   │   ├── redis/
│   │   ├── traefik/
│   │   ├── cert-manager/
│   │   └── secrets/
│   └── overlays/
│       ├── staging/
│       └── production/
└── scripts/
    ├── smoke-test.ps1
    └── rollback.ps1

.github/
└── workflows/
    └── deploy-gke.yml
```

**Structure Decision**: Add a new `deploy/` tree for Kubernetes/Kustomize deployment assets and helper scripts, leaving application code under the existing `backend/`, `frontend/`, and `supabase/` directories. Place the GitHub Actions workflow under `.github/workflows/` rather than the currently empty `.github/deploy.yml` file.

## Complexity Tracking

No constitution violations identified. Notable tradeoffs are documented in `research.md`: self-hosted Redis instead of Memorystore, fixed replicas before HPA, CPU-only inference, and one shared Traefik LoadBalancer.
