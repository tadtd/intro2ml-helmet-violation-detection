# Quickstart Guide

**Feature**: Helmet Violation Detection System
**Branch**: `001-detect-helmet-violations`

---

## 1. Local Development Prerequisites

Ensure the following tools are installed locally:
* **Docker & Docker Compose**: For local monorepo orchestration.
* **`uv`**: For rapid Python virtual environment and dependency management.
* **Node.js (v18+) & `npm`**: For running the Next.js frontend locally.

---

## 2. Local Stack Setup (Docker Compose)

The monorepo provides a `docker-compose.yml` at the repository root containing:
* Redis (Event broker & Celery backend)
* Traefik (API Gateway)
* PostgreSQL (Local mock of Supabase DB schema)
* MinIO (Local mock of S3 storage)
* Next.js (Frontend)
* Auth Service, Ingestion Service, Orchestrator, Notification, and Query services
* Inference Worker (runs on CPU locally)

To start the local stack:

```bash
# 1. Clone the project and navigate to root
cd intro2ml-helmet-violation-detection

# 2. Build and spin up all services
docker compose up --build
```

The services are exposed locally at:
* **Frontend UI**: `http://localhost:3000`
* **API Gateway Route**: `http://localhost:8000`

---

## 3. Running Automated Tests Local-Side

We write backend tests using `pytest`. The python services are configured using `uv`.

### 3.1 Initializing Virtual Environments
For any microservice (e.g., `backend/inference-service/`):

```bash
cd backend/inference-service

# Create virtual environment using uv
uv venv

# Activate venv (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Install dev dependencies
uv pip install -e ".[dev]"
```

### 3.2 Running the Test Suite
Run tests (including contract, integration, and mocks verification):

```bash
# Run tests inside service directory
pytest
```

---

## 4. GKE Staging Deployment Verification

Before pushing to main, developers can verify the Kubernetes manifests locally using Minikube or directly in the GCP console:

```bash
# 1. Authenticate with GKE cluster
gcloud container clusters get-credentials helmet-detection-cluster --region us-central1

# 2. Apply secrets manifest (decrypted from secrets store)
kubectl apply -f k8s/secrets.yaml

# 3. Deploy/Upgrade Helm chart
helm upgrade --install helmet-system k8s/helm-chart \
  --set global.image.tag=latest \
  --values k8s/values-staging.yaml
```
