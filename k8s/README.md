# Kubernetes Handoff

These manifests are reviewable GKE handoff artifacts for the Helmet Violation
Detection monorepo. They are not a production rollout plan and do not provision
GKE, DNS, TLS, load balancers, Artifact Registry, IAM, or secrets.

## Artifact Purpose

| File | Purpose |
|------|---------|
| `namespace.yaml` | Namespace placeholder for the deployment. |
| `redis.yaml` | Redis Deployment and Service for Celery broker/result backend. |
| `api.yaml` | FastAPI Deployment and Service with `/health` probes. |
| `worker.yaml` | Celery worker Deployment with Redis readiness check. |
| `frontend.yaml` | Optional Next.js Deployment and Service; not required for this feature. |
| `secrets.example.yaml` | Placeholder secret names and keys only. |
| `kustomization.yaml` | Grouping file for review or future apply flow. |

The existing `.github/deploy.yml` is empty/nonstandard and is not the target
workflow. The target workflow outline is `.github/workflows/deploy-gke.yml`.

## Review Order

1. Complete the local Docker Compose smoke test in `docs/devops-smoke-test.md`.
2. Confirm Supabase setup and bucket policy decisions in `docs/supabase-setup.md`.
3. Inspect `k8s/secrets.example.yaml` and create real secrets outside git.
4. Replace image placeholders in `api.yaml`, `worker.yaml`, and optionally
   `frontend.yaml`.
5. Review `k8s/kustomization.yaml`.
6. Review `.github/workflows/deploy-gke.yml` before enabling deployment.

## Secret Placeholders

Real values must not be committed. Local values stay in untracked `.env` files.
CI should use GitHub Actions workload identity for GCP access. Cluster workloads
may consume GCP Secret Manager references through the infrastructure owner's
approved process or documented Kubernetes Secret placeholders.

Example Kubernetes Secret creation commands:

```powershell
kubectl create namespace helmet-violation --dry-run=client -o yaml | kubectl apply -f -

kubectl -n helmet-violation create secret generic helmet-api-secrets `
  --from-literal=SUPABASE_URL="<SUPABASE_URL>" `
  --from-literal=SUPABASE_ANON_KEY="<SUPABASE_ANON_KEY>" `
  --from-literal=SUPABASE_SERVICE_ROLE_KEY="<SUPABASE_SERVICE_ROLE_KEY>" `
  --from-literal=SUPABASE_JWT_SECRET="<SUPABASE_JWT_SECRET>" `
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n helmet-violation create secret generic helmet-frontend-public-config `
  --from-literal=NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY="<NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY>" `
  --dry-run=client -o yaml | kubectl apply -f -
```

The example commands contain placeholders only. Use a secure approved channel to
provide real values at execution time.

## Image Placeholders

Replace these placeholder image references before applying manifests:

```text
REGION-docker.pkg.dev/PROJECT_ID/REPOSITORY/helmet-api:TAG
REGION-docker.pkg.dev/PROJECT_ID/REPOSITORY/helmet-worker:TAG
REGION-docker.pkg.dev/PROJECT_ID/REPOSITORY/helmet-frontend:TAG
```

The GitHub Actions outline builds API and worker images by default and includes
an optional frontend build gate.

## Smoke Review

These artifacts assume local validation is complete first:

```powershell
docker compose up --build
docker compose ps
Invoke-RestMethod -Uri http://localhost:8000/health -Method Get
```

For cluster review, the infrastructure owner can inspect or dry-run manifests:

```powershell
kubectl kustomize .\k8s
kubectl apply --dry-run=server -k .\k8s
```

Server-side dry-run requires an existing cluster and the real secrets to be
created outside git.

## Failure Notes

- Missing secrets: create `helmet-api-secrets` and optional
  `helmet-frontend-public-config` outside git, then retry.
- Placeholder image errors: replace all `REGION`, `PROJECT_ID`, `REPOSITORY`,
  and `TAG` placeholders with approved Artifact Registry image names.
- Redis unavailable: inspect `helmet-redis` rollout and confirm the API/worker
  `REDIS_URL` points at `redis://helmet-redis:6379/0`.
- API health failure: inspect `helmet-api` logs and verify Supabase secret keys.
- Worker not ready: inspect `helmet-worker` logs for Redis or Supabase
  configuration errors.

## Non-Goals

This feature does not require production rollout execution, DNS, TLS, GKE
cluster provisioning, Terraform, Helm, ArgoCD, External Secrets, ML inference
implementation, or frontend workflow implementation.
