# Deployment Contract: Google Cloud GKE

## Runtime Topology

The deployment MUST create or target:

- One GKE Autopilot cluster in `asia-southeast1`
- One namespace per environment:
  - `helmet-staging`
  - `helmet-production`
- One Artifact Registry Docker repository in `asia-southeast1`
- One Traefik public `LoadBalancer` Service
- One Redis StatefulSet per environment with a small PVC
- GCP Secret Manager secrets for Supabase, DuckDNS, and deployment credentials
- Workload Identity Federation bindings from Kubernetes service accounts to GCP IAM principals

## Workload Contract

| Workload | Image Source | Kubernetes Kind | Exposure | Initial Replicas | Notes |
|----------|--------------|-----------------|----------|------------------|-------|
| `frontend` | project image | Deployment | Public via Traefik | 1 | Next.js Dashboard |
| `ingestion` | project image | Deployment | Public API via Traefik | 1 | Upload API |
| `auth` | project image | Deployment | Internal ClusterIP | 1 | Auth API and gRPC |
| `dashboard` | project image | Deployment | Internal, routed only for approved API paths | 1 | Violation/dashboard API |
| `notification` | project image | Deployment | Internal, routed only for approved WebSocket path | 1 | Status WebSocket |
| `orchestration` | project image | Deployment | Internal ClusterIP | 1 | Job lifecycle/retention |
| `inference-worker` | project image | Deployment | Internal worker only | 1 | Celery worker with larger CPU-only profile |
| `realtime-stream` | inference image | Deployment | Routed only for approved camera stream path | 1 | Uvicorn stream server |
| `redis` | `redis:7-alpine` | StatefulSet | Internal ClusterIP | 1 | Append-only with PVC |
| `traefik` | `traefik:v3.x` | Deployment/Service | Public LoadBalancer | 1 | Single ingress controller |

## Public Route Contract

The initial public route set is:

| Public Path | Target | Protocol | Demo/Production Requirement |
|-------------|--------|----------|-----------------------------|
| `/` | `frontend` | HTTPS | DuckDNS + Let's Encrypt |
| `/api/v1/videos` | `ingestion` | HTTPS | DuckDNS + Let's Encrypt |
| `/api/v1/violations` | `dashboard` | HTTPS | DuckDNS + Let's Encrypt |
| `/ws/status` | `notification` | WSS | DuckDNS + Let's Encrypt |
| `/ws/camera` | `realtime-stream` | WSS | DuckDNS + Let's Encrypt |

Direct public exposure is forbidden for Auth, Orchestration, Inference Worker, Redis, and any unapproved service path.

## Secret Contract

Runtime secrets MUST be stored in Secret Manager and consumed through Workload Identity Federation or an approved sync mechanism during deploy.

Required secret names:

- `helmet-supabase-url`
- `helmet-supabase-anon-key`
- `helmet-supabase-service-role-key`
- `helmet-supabase-jwt-secret`
- `helmet-supabase-video-bucket`
- `helmet-supabase-storage-bucket`
- `helmet-duckdns-token`

Rules:

- No plaintext secret values in Git-tracked manifests.
- No service account JSON keys.
- CI logs must not echo secret values.
- Each environment may use separate secret versions or separate secret names.

## Resource Profile Contract

Initial planning placeholders to be finalized in tasks:

| Profile | Intended Workloads | Initial Intent |
|---------|--------------------|----------------|
| `light-api` | Auth, Ingestion, Dashboard API, Orchestration, Notification | Conservative CPU/memory for low traffic |
| `frontend` | Next.js frontend | Conservative CPU/memory for one demo workload |
| `redis-small` | Redis StatefulSet | Small persistent queue/cache footprint |
| `inference-cpu` | Inference Worker, Realtime Stream if needed | Larger CPU/memory for ONNX Runtime and OpenCV |
| `traefik-small` | Traefik | Conservative ingress profile |

Every profile MUST be reviewed after smoke tests using CPU, memory, restart count, and processing duration.

## Readiness Contract

Deployment is not demo-ready until all conditions pass:

- Budget alerts exist at 50%, 90%, and 100% of the $300 free-trial budget.
- Kustomize overlay renders without errors.
- Images are tagged with the deployed commit SHA.
- All required workloads are healthy.
- DuckDNS resolves to the Traefik LoadBalancer IP.
- Let's Encrypt certificate is valid.
- Login, upload, processing, results review, dashboard health, WebSocket status, and rollback smoke checks pass.
