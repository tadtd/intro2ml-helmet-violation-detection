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
* **`ingestion`**: Handles video upload REST endpoints and video/job listing APIs.
* **`inference`**: Celery worker performing ONNX-runtime deep learning model inference (YOLO, RT-DETR, Faster R-CNN) with object tracking and violation association heuristics.
* **`realtime`**: Reuses the inference image but runs a uvicorn WebSocket server (`/ws/camera`). It decodes any RTSP/HLS/file source, runs live ONNX detection, and streams annotated JPEG frames to the browser.
* **`notification`**: Redis subscriber broadcasting real-time alert updates and job status logs over WebSockets.
* **`dashboard`**: Provides paginated REST APIs for violation auditing with gRPC-based role authorization (RLS enforcement).
* **`orchestration`**: Periodically prunes raw files from Supabase Storage based on a 3-day retention policy.
* **`frontend` (Next.js)**: Modern responsive dashboard for live camera viewing, video uploads, and violation auditing.

---

## 📹 Live Camera Monitoring

The **Giám sát camera** page runs a live WebSocket stream that decodes a source,
runs the ONNX model frame-by-frame, and overlays detection boxes plus a running
violation count. The source can be:

* a bundled demo clip,
* **any RTSP or HLS URL**, or
* **a YouTube live/video URL** — the backend resolves it with `yt-dlp` and runs
  detection on it, so pasting a live traffic stream works out of the box.

The same pipeline plugs straight into a real camera feed. Override the
per-location demo sources with `CAMERA_SRC_CAM_01/02/03` env vars.

---

## 🛠️ Prerequisites

* **Docker & Docker Compose** (Required for containerized runtime)
* **Python 3.13+** and **`uv`** (Required for local workspace scripting and running pytest suites)

---

## ⚙️ Configuration Setup

### 1. Supabase Initialization
1. Create a project in [Supabase](https://supabase.com/).
2. Link the local project if needed:
   ```bash
   npx supabase link --project-ref <project-ref>
   ```
3. Apply the canonical database migrations:
   ```bash
   npx supabase db push
   ```

The database source of truth is `supabase/`:
* `supabase/migrations/`: schema, RLS policies, helper functions, and storage buckets.
* `supabase/tests/`: pgTAP tests and benchmark seed SQL.

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

By default `docker-compose.yml` sets `USE_STUB_INFERENCE=true`, so the stack runs with a mock detector and needs no weights.

To run real inference, place the exported ONNX model weights under `backend/inference/weights/`:
* `yolo_best.onnx`
* `rtdetr_best.onnx`
* `fasterrcnn_best.onnx`

Then set `USE_STUB_INFERENCE=false` on the `inference` service and rebuild (the weights are baked into the image, so `docker compose up` alone will not pick them up):

```bash
docker compose up --build
```

---

## 🧪 Running the Test Suite

We use `pytest` for unit and integration testing. Run all workspace suites from the root directory:

```bash
PYTHONPATH=backend uv run pytest backend/ingestion/ backend/inference/ backend/notification/ backend/dashboard/ backend/orchestration/
```

On PowerShell:

```powershell
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

Google Cloud deployment documentation and assets are located in:

- [`docs/deployment/google-cloud.md`](docs/deployment/google-cloud.md) for the deployment scope, implementation order, owner checklist, and incident runbook.
- [`deploy/k8s/`](deploy/k8s/) for the production-ready Kubernetes manifests managed with Kustomize.
- [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) for the GKE deployment CI/CD workflow pipeline using Artifact Registry and Workload Identity.
- [`deploy/scripts/win/`](deploy/scripts/win/) for validation, setup, and smoke testing utilities.

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
