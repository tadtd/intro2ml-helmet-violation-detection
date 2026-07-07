# Helmet Violation Detection

### 🌟 Project Overview
This application is designed to **automatically detect traffic safety violations, specifically motorcycle riders not wearing safety helmets**, from both pre-recorded video uploads and simulated real-time live camera feeds.

Key functionalities:
* **Automated Violation Detection**: Analyzes video frames asynchronously to detect motorbikes and riders. It correlates motorcycle tracks with non-helmet detections using box-overlap (IoU) heuristics.
* **Crop Upload & Proof Storage**: Auto-generates tight composite crop bounding boxes containing both the motorcycle and the rider without a helmet, uploading the image to Supabase Cloud Storage as permanent visual audit proof.
* **Realtime Monitoring & WS Alerts**: Pipes live camera feeds to operators and pushes instant WebSocket alerts (`new_violation_alert`) with Vietnamese/English text-to-speech audio warnings whenever a violation is captured.
* **Violation Auditing Dashboard**: A secure web dashboard for operators and administrators to query and filter violation reports, view cropped proof images, and configure model inference types.

---

## 🏗️ System Architecture

The application is structured into the following services:

* **`api-gateway` (Traefik)**: Entrypoint proxying requests and WebSocket streams to backend services.
* **`auth`**: Handles operator/admin profiles and token verification over gRPC on port `50051`.
* **`ingestion`**: Handles video upload REST endpoints and pipes raw MJPEG camera frame streams over WebSockets.
* **`inference`**: Celery worker performing ONNX-runtime deep learning model inference (YOLO, RT-DETR, Faster R-CNN) with object tracking and violation association heuristics.
* **`notification`**: Redis subscriber broadcasting real-time alert updates and job status logs over WebSockets.
* **`dashboard`**: Provides paginated REST APIs for violation auditing with gRPC-based role authorization (RLS enforcement).
* **`orchestration`**: Periodically prunes raw files from Supabase Storage based on a 3-day retention policy.
* **`frontend` (Next.js)**: Modern responsive dashboard for live camera viewing, video uploads, and violation auditing.

---

## 🛠️ Prerequisites

* **Docker & Docker Compose** (Required for containerized runtime)
* **Python 3.13+** and **`uv`** (Required for local workspace scripting and running pytest suites)

---

## ⚙️ Configuration Setup

### 1. Supabase Initialization
1. Create a project in [Supabase](https://supabase.com/).
2. Create two storage buckets:
   * **`videos`**: Access level set to **Private** (stores raw uploaded mp4s).
   * **`violations`**: Access level set to **Public** (stores cropped violation images).
3. Apply the SQL schema scripts found inside `backend/supabase/schema/` in order using the Supabase SQL editor:
   * `01_profiles.sql`
   * `02_videos.sql`
   * `03_violations.sql`

### 2. Environment Configuration
Copy `.env.example` to `.env` in the root directory and supply your Supabase credentials:
```bash
cp .env.example .env

SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
SUPABASE_JWT_SECRET=your_supabase_jwt_secret
```

---

## 🚀 Running the Stack

To start the entire local stack (all microservices, Redis database, API gateway, and frontend):

```bash
docker compose up --build
```

### Access Ports
* **Frontend Application**: Access at [http://localhost:3000](http://localhost:3000)
* **Traefik API Gateway**: Routed at [http://localhost:8000](http://localhost:8000)

---

## 👥 Seeding Test Users

To seed the initial user accounts (Operator & Admin) into Supabase Auth for logging into the dashboard:

```bash
# Sync local package dependencies
uv sync

# Run the seed script
uv run backend/seed_users.py
```
* **Operator Account**: `operator@system.com` / `password123`
* **Admin Account**: `admin@system.com` / `password123`

---

## 📦 Model Weights (Optional)

For local model evaluations (bypassing the mock detector `USE_STUB_INFERENCE=true`), place the exported ONNX model weights under `backend/weights/`:
* `yolo_best.onnx`
* `rtdetr_best.onnx`
* `fasterrcnn_best.onnx`

---

## 🧪 Running the Test Suite

We use `pytest` for unit and integration testing. Run all workspace suites from the root directory:

```powershell
# Set pythonpath and run pytest
$env:PYTHONPATH="backend"
uv run pytest backend/ingestion/ backend/inference/ backend/notification/ backend/dashboard/ backend/orchestration/
```
The frontend runs at `http://localhost:3000`; the API gateway runs at `http://localhost:8000`.

## 🧪 Local Smoke Test

After `docker compose up --build`, verify the local runtime before Kubernetes or
CI/CD work. Full PowerShell smoke-test steps are in
[docs/devops-smoke-test.md](docs/devops-smoke-test.md).

```powershell
docker compose ps
```

The Compose stack must show Redis, Traefik, auth, ingestion, notification, dashboard, orchestration, inference, and frontend services running. Any
infrastructure change must update these local run and smoke-test instructions
when the commands or expected checks change.

## 📦 Deployment Artifact Review

Production handoff artifacts are reviewable outlines, not a production rollout.
Review them after the local Docker Compose smoke test passes:

- [k8s/README.md](k8s/README.md) for GKE manifest handoff, secret placeholder
  creation, image placeholder replacement, and failure notes.
- [k8s/kustomization.yaml](k8s/kustomization.yaml) for the manifest grouping.
- [.github/workflows/deploy-gke.yml](.github/workflows/deploy-gke.yml) for the
  GKE deployment pipeline outline using Artifact Registry and workload identity.

The existing `.github/deploy.yml` file is empty/nonstandard and is not the
target workflow. Terraform, Helm, ArgoCD, and External Secrets are not required
for this feature.

## 🔒 Security Rules

- Frontend code uses only `NEXT_PUBLIC_SUPABASE_URL` and
  `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.
- Backend services read Supabase service role credentials only
  from environment variables or a secret manager.
- Kubernetes and CI/CD files must use secret placeholders or secret-manager
  references with documented creation steps, not hardcoded secret values.

## 🏋️ Model Weights

Place exported ONNX files in `backend/inference/weights/`:

- `yolo_best.onnx`
- `rtdetr_best.onnx`
- `fasterrcnn_best.onnx`

The wrapper classes are wired for ONNX Runtime, but final output parsing depends
on the exported model tensor shape and class mapping.
