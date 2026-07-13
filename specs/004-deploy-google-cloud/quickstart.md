# Quickstart: Validate Google Cloud Deployment Plan

This guide describes the validation path for the GKE deployment feature. It is intentionally a runbook for future implementation tasks, not a complete deployment script.

## Prerequisites

- Google Cloud project with free-trial billing enabled.
- Budget alerts configured at 50%, 90%, and 100% of the $300 budget before any cluster or load balancer is created.
- Google Cloud APIs enabled for GKE, Artifact Registry, Secret Manager, IAM, and Cloud Billing.
- GitHub repository configured for GitHub Actions.
- DuckDNS subdomain and token available.
- Supabase project and required connection values available.
- Local tools: Docker, Docker Compose, `uv`, Node/npm, `gcloud`, `kubectl`, and Kustomize support through `kubectl kustomize` or `kustomize`.

## 1. Validate Local Baseline

From the repository root:

```bash
docker compose up --build
```

Expected:

- Redis, Traefik, backend services, inference worker, realtime stream, and frontend start.
- Frontend is reachable locally.
- Upload/status/result flows can be smoke-tested with local or stub credentials as appropriate.

Run backend and frontend checks:

```bash
cd backend
uv run pytest

cd ../frontend
npm run lint
npm run build
```

Expected:

- Backend tests pass.
- Frontend lint and build pass.

## 2. Validate Cloud Safeguards

Before deployment:

```bash
gcloud billing budgets list --billing-account <BILLING_ACCOUNT_ID>
```

Expected:

- Budget alerts exist for 50%, 90%, and 100% of the $300 free-trial budget.
- Maintainer recipients are configured.

## 3. Validate Artifact Registry

Expected repository format:

```text
asia-southeast1-docker.pkg.dev/<PROJECT_ID>/<REPOSITORY>/<SERVICE>:<COMMIT_SHA>
```

Validation:

```bash
gcloud artifacts repositories list --location=asia-southeast1
```

Expected:

- Docker repository exists in `asia-southeast1`.
- GitHub Actions deploy identity can push images.

## 4. Validate GKE Cluster Access

```bash
gcloud container clusters get-credentials <CLUSTER_NAME> --region asia-southeast1
kubectl get namespaces
```

Expected:

- Cluster credentials are available.
- `helmet-staging` and/or `helmet-production` namespaces exist after manifests are applied.

## 5. Validate Secret Access

```bash
gcloud secrets list --filter="name:helmet-"
```

Expected:

- Required Supabase, JWT, and DuckDNS secrets exist.
- Workload Identity Federation bindings allow only approved Kubernetes service accounts to read required secrets.
- No service account JSON key files are used.

## 6. Render Manifests

```bash
pwsh deploy/scripts/win/validate-manifests.ps1
```

Expected:

- Both overlays render without errors.
- Project images use commit-SHA tags.
- Public exposure exists only through Traefik.
- No plaintext secret values appear in output.
- No HPA or GPU resources appear in the initial manifests.

## 7. Deploy Staging

The GitHub Actions workflow on `main` should:

1. Run tests and builds.
2. Push commit-SHA-tagged images to Artifact Registry.
3. Apply `deploy/k8s/overlays/staging`.
4. Wait for rollout.
5. Run smoke checks.

Manual validation:

```bash
kubectl -n helmet-staging get pods
kubectl -n helmet-staging get svc
kubectl -n helmet-staging rollout status deployment/frontend
kubectl -n helmet-staging rollout status deployment/ingestion
pwsh deploy/scripts/win/validate-exposure.ps1 -Overlay staging
```

Expected:

- All expected workloads are healthy.
- Only Traefik has public LoadBalancer exposure.

## 8. Validate DNS And TLS

Early smoke tests may use the temporary LoadBalancer IP. Demo-ready validation requires DuckDNS and TLS:

```bash
kubectl -n helmet-staging get certificates
curl -I https://<yourname>.duckdns.org
```

Expected:

- cert-manager certificate is ready.
- DuckDNS resolves to the Traefik LoadBalancer IP.
- HTTPS returns a successful response for the frontend.

## 9. Run End-to-End Smoke Checks

Required checks:

- Open the Dashboard login page through the DuckDNS HTTPS URL.
- Log in with an authorized test user.
- Upload a supported sample video through the Ingestion API.
- Confirm job status moves from pending/queued to processing and then done or failed.
- Review violation results.
- Confirm `/api/v1/violations` returns authorized data.
- Confirm `/ws/status` connects over WSS.
- Confirm internal-only services are not directly reachable from the public internet.
- Review CPU, memory, restart count, and processing duration for each workload.

Scripted checks:

```bash
pwsh deploy/scripts/win/smoke-test.ps1 -BaseUrl https://<yourname>.duckdns.org -Namespace helmet-staging
pwsh deploy/scripts/win/collect-smoke-metrics.ps1 -Namespace helmet-staging
```

Expected:

- Smoke checks pass before a release is marked known-good.
- Any failure blocks demo-ready promotion.

## 10. Validate Rollback

Rollback target:

```text
previous known-good commit SHA
```

Expected workflow behavior:

1. Redeploy image tags for the previous known-good SHA.
2. Apply the same Kustomize overlay.
3. Wait for rollout.
4. Re-run smoke checks.

Manual validation:

```bash
pwsh deploy/scripts/win/rollback.ps1 -CommitSha <KNOWN_GOOD_SHA> -Environment staging -Namespace helmet-staging
kubectl -n helmet-staging get deploy -o wide
```

Expected:

- Running images match the rollback SHA.
- Smoke checks pass within the 10-minute rollback target.

## 11. Promotion Readiness

A release is ready for demo/production-style use only when:

- Budget alerts are configured.
- Local checks pass.
- CI/CD workflow passes.
- Staging rollout succeeds.
- DuckDNS + Let's Encrypt TLS is valid.
- End-to-end smoke checks pass.
- Running images are traceable to a commit SHA.
- Previous known-good SHA is recorded for rollback.
