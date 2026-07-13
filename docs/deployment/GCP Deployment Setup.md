# GCP Deployment Setup — Helmet Violation Detection

This document records all the setup steps for GCP + GitHub to deploy the system (Auth, Ingestion, Inference Worker, Orchestration, Notification, Dashboard) to GKE Autopilot.

## Architecture Decisions

| Item | Choice | Why |
|---|---|---|
| Cluster mode | GKE **Autopilot** | You only pay for actual pod resource requests, not idle nodes — safer for a free-trial budget |
| Region | `asia-southeast1` (Singapore) | Closest GCP region to Vietnam |
| Redis | Self-hosted in-cluster (StatefulSet + PVC) | Cheaper than managed Memorystore, sufficient for a course project |
| Secrets | GCP Secret Manager | Safer than plain Kubernetes Secrets, has audit logging |
| Ingress | Traefik in-cluster + a single LoadBalancer | Avoids paying for multiple Load Balancers (~$18-25/month each) if every service had its own Ingress |
| Autoscaling | None yet, fixed replicas (1-2 pods/service) | Traffic is low; HPA adds complexity that isn't needed yet — add later once real usage data exists |
| Manifest tooling | Kustomize | Fits multiple services + multiple environments without Helm's extra templating complexity |
| Namespace strategy | Per-environment (staging/production) in one cluster | Cheaper than separate clusters, still isolates secrets/config |
| Domain/TLS | DuckDNS (free) + Let's Encrypt via cert-manager | Free and sufficient for a course project |
| Resource requests | Conservative baseline for API/Dashboard, larger CPU-only profile for Inference Worker | Avoids OOMKilled for ONNX/OpenCV, avoids overpaying for lightweight services |
| Image tagging | Commit SHA | Every deployed version is traceable; rollback = redeploy the previous known-good SHA |

---

## Part 1 — GCP Setup

### 1.1 Create the project
```bash
gcloud projects create helmet-detection-2026 --name="Helmet Violation Detection"
gcloud config set project helmet-detection-2026
```
**Why:** the project is the container for all resources (cluster, registry, secrets...) and billing. `config set project` makes every subsequent command default to this project, so you don't need `--project` every time.

### 1.2 Link a billing account
Done via Console: `console.cloud.google.com/billing/linkedaccount?project=helmet-detection-2026`
**Why:** most APIs (Container, Artifact Registry...) require billing to be enabled before they can be turned on, even when running on free-trial credit.

Verify:
```bash
gcloud billing projects describe helmet-detection-2026
```

### 1.3 Set a budget alert
Console: `console.cloud.google.com/billing/budgets` → create a budget for the project, set alerts at 50%/90%/100% of your available credit.
**Why:** this is only an **email notification**, not a hard cap — GCP has no built-in feature to automatically stop spending. The alert lets you proactively check before burning through all your credit, which matters especially if the account is already in "full account" (pay-as-you-go after credit runs out) mode rather than a plain free trial.

### 1.4 Enable required APIs
```bash
gcloud services enable container.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudresourcemanager.googleapis.com
```
**Why:** GCP disables most APIs by default to prevent unintended charges — each service (GKE, Artifact Registry, Secret Manager) needs its corresponding API enabled before use.

### 1.5 Create Artifact Registry
```bash
gcloud artifacts repositories create helmet-repo \
  --repository-format=docker \
  --location=asia-southeast1
```
**Why:** this is the "warehouse" for Docker images on GCP — it needs to exist before CI/CD has anywhere to push images to.

Verify:
```bash
gcloud artifacts repositories list --location=asia-southeast1
```

### 1.6 Create the GKE Autopilot cluster
```bash
gcloud container clusters create-auto helmet-cluster \
  --region=asia-southeast1
```
**Why:** this is the actual infrastructure that runs containers — a Kubernetes cluster with Google-managed nodes (Autopilot). This command takes about 5-10 minutes and creates an empty cluster (no services running yet).

Verify:
```bash
gcloud container clusters list --region=asia-southeast1
```

### 1.7 Create a Service Account for GitHub Actions
```bash
gcloud iam service-accounts create github-deployer \
  --display-name="GitHub Actions Deployer"
```
**Why:** GitHub Actions needs its own "robot account" to authenticate with GCP when building/deploying automatically — not your personal account, which reduces security risk and makes it easy to revoke access if needed.

Grant permissions:
```bash
gcloud projects add-iam-policy-binding helmet-detection-2026 \
  --member="serviceAccount:github-deployer@helmet-detection-2026.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding helmet-detection-2026 \
  --member="serviceAccount:github-deployer@helmet-detection-2026.iam.gserviceaccount.com" \
  --role="roles/container.developer"

gcloud projects add-iam-policy-binding helmet-detection-2026 \
  --member="serviceAccount:github-deployer@helmet-detection-2026.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```
**Why each role:**
- `artifactregistry.writer` — lets CI/CD push Docker images
- `container.developer` — lets CI/CD deploy (kubectl apply) to GKE
- `secretmanager.secretAccessor` — lets pods in the cluster read real secrets at runtime

### 1.8 Create a key for the Service Account
```bash
gcloud iam service-accounts keys create github-key.json \
  --iam-account=github-deployer@helmet-detection-2026.iam.gserviceaccount.com
```
**Why:** GitHub needs this key to "log in" to GCP on your behalf when running a workflow. This file is extremely sensitive — **never commit it to Git**; only paste its contents into GitHub Secrets, then delete it from your machine (`rm github-key.json`).

### 1.9 Upload real secrets to Secret Manager
```bash
echo -n "real-value" | gcloud secrets create supabase-key --data-file=-
echo -n "real-value" | gcloud secrets create jwt-secret --data-file=-
```
**Why:** this is the secure storage location for real secrets (Supabase key, JWT secret...) that currently live in your local `.env` — the cluster will read from here at runtime instead of hardcoding values or leaking them in code.

---

## Part 2 — GitHub Setup

### 2.1 Add GitHub Actions Settings
Repo → Settings → Secrets and variables → Actions → Secrets → New repository secret:
- `GCP_SA_KEY` = the entire contents of `github-key.json`

Repo → Settings → Secrets and variables → Actions → Variables → New repository variable:
- `GCP_PROJECT_ID` = `helmet-detection-2026`
- `GKE_REGION` = `asia-southeast1`
- `GKE_CLUSTER` = `helmet-cluster`
- `ARTIFACT_REGISTRY_REPOSITORY` = `helmet-repo`
- `DUCKDNS_DOMAIN` = `dtdat-nthv.duckdns.org`

**Why:** GitHub Actions has no default access to your local machine or GCP — it needs these values to know where to deploy and what permissions to authenticate with.

### 2.2 Write the GitHub Actions workflow
The `.github/workflows/deploy.yml` file (to be written in detail later) will:
1. Checkout code
2. Build the Docker image, tagged with the commit SHA
3. Push the image to Artifact Registry
4. `kubectl apply` (via a Kustomize overlay) to deploy to GKE

**Why tag with commit SHA:** every deployment can be traced back to the exact commit running on the cluster — rollback is just redeploying the previous known-good SHA, instead of guessing "what was the previous version" as you would with a `latest` tag.

---

## Part 3 — DNS & TLS (DuckDNS)

### 3.1 Required order of operations
1. Deploy Traefik to the cluster first
2. `kubectl get svc traefik` → get the real External IP (assigned by GCP, different from your personal machine's IP)
3. Go to DuckDNS, point your subdomain (`dtdat-nthv.duckdns.org`) to that exact IP (the "update ip" button)
4. Fill in the real domain in `Certificate.yaml` (replacing the placeholder), then `kubectl apply`

**Why this order is mandatory:** cert-manager requests a certificate from Let's Encrypt by having Let's Encrypt send a verification request directly to the domain (HTTP-01 challenge). If the domain isn't yet pointing to the cluster's IP, that verification request fails and the certificate won't be issued — so the domain must point correctly **first**, and the two steps can't be done in parallel or reversed.

---

## Important Cost Notes

- Your account may already be in **"full account"** mode (pay-as-you-go once credit runs out) rather than a plain free trial with a hard limit — check by looking at whether your billing overview shows "Use any remaining credits, then pay as you go."
- GCP Console has no built-in "hard cap" feature — budget alerts only send emails, they don't automatically stop resources.
- **The biggest cost risk:** leaving the cluster/Load Balancer running when not needed. Delete it when you're done for the day:
```bash
gcloud container clusters delete helmet-cluster --region=asia-southeast1
```
- Check billing every 2-3 days at `console.cloud.google.com/billing`.
