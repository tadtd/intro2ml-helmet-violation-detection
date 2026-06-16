# Plan: Helmet Violation Detection System

## 1. Overview

A web application that allows:

- Uploading a video to detect violations (choosing one of 3 models: YOLO / RT-DETR / Faster R-CNN)
- Continuous real-time camera detection
- A dashboard showing detected violations (image, timestamp, track_id, model used)
- Login and role-based access (admin / operator)

## 2. Tech Stack

| Component | Technology |
| --- | --- |
| Frontend | Next.js |
| Backend API | FastAPI |
| Task queue (video upload processing) | Celery + Redis |
| Database | Supabase (Postgres) — free tier |
| Auth | Supabase Auth — free tier |
| Storage (violation images) | Supabase Storage — free tier |
| Realtime dashboard updates | Supabase Realtime — free tier |
| Containerization | Docker |
| Package manager | uv (`pyproject.toml` + `uv.lock`, no `requirements.txt`) |
| Deployment compute | GCP (GKE) — using $300 free trial |
| CI/CD | GitHub Actions |
| Models | YOLO, RT-DETR, Faster R-CNN — converted to ON |

## 3. Overall Architecture

```
Next.js
  ├── Login/Signup → Supabase Auth
  ├── "Upload video" tab → FastAPI /videos/upload → Celery task
  ├── "Camera realtime" tab → WebSocket → FastAPI live inference
  └── Violations dashboard → Supabase Realtime subscription + REST API

FastAPI (GKE)
  ├── Middleware: verify Supabase JWT
  ├── /videos/upload  → push task to Celery (Redis broker)
  ├── /ws/camera       → real-time inference, log violations
  └── /violations      → query Supabase Postgres

Celery worker (GKE, autoscaled by queue length)
  ├── Load ONNX model based on model_name (yolo/rtdetr/fasterrcnn)
  ├── Inference via ONNX Runtime (no PyTorch/torch needed) + tracking
  ├── Association logic: link helmet/non-helmet boxes to motorbike boxes
  ├── Save cropped violation images → Supabase Storage
  └── Insert violation metadata → Supabase Postgres

Redis (GKE) → Celery broker
```

## 4. Database Schema (Supabase Postgres)

```sql
-- auth.users: provided by Supabase Auth

create table profiles (
  id uuid references auth.users primary key,
  role text default 'operator', -- 'admin' | 'operator'
  full_name text
);

create table videos (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id),
  filename text,
  model_used text,
  status text default 'pending', -- pending | processing | done
  created_at timestamptz default now()
);

create table violations (
  id uuid primary key default gen_random_uuid(),
  video_id uuid references videos(id), -- null if from real-time camera
  user_id uuid references auth.users(id),
  track_id int,
  model_used text,
  image_url text,
  timestamp timestamptz default now()
);

-- Row Level Security
alter table violations enable row level security;
create policy "view own or admin" on violations
  for select using (
    auth.uid() = user_id
    or exists (select 1 from profiles where id = auth.uid() and role = 'admin')
  );
```

## 5. Violation Detection Logic (shared across all 3 models)

1. Normalize the output of all 3 models into a common format:
    
    ```python
    [{"class": "non-helmet", "box": [x1,y1,x2,y2], "conf": 0.92}, ...]
    ```
    
2. Tracking: assign a persistent `track_id` to each motorbike across frames
    - YOLO/RT-DETR: use built-in `.track()` (ByteTrack/BoT-SORT)
    - Faster R-CNN: implement a simple custom IoU-tracker
3. Association: for each `motorbike` box, find the nearest `helmet`/`non-helmet` box (via IoU or centroid distance)
4. Decision: if a `motorbike` is linked to a `non-helmet` box → violation
5. Save: cropped violation image + track_id + timestamp + model_used

## 6. Project Structure (Monorepo)

```
project/
├── frontend/                  # Next.js
│   ├── app/
│   │   ├── login/
│   │   ├── dashboard/
│   │   ├── upload/
│   │   └── camera/
│   └── lib/supabase.ts
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── auth.py             # verify Supabase JWT
│   │   ├── models/
│   │   │   ├── yolo_wrapper.py
│   │   │   ├── rtdetr_wrapper.py
│   │   │   └── fasterrcnn_wrapper.py
│   │   ├── tracker.py          # shared IoU-tracker
│   │   ├── violation_logic.py  # association + decision
│   │   ├── tasks.py            # Celery tasks
│   │   └── routes/
│   ├── weights/                # ONNX models (converted offline)
│   │   ├── yolo_best.onnx
│   │   ├── rtdetr_best.onnx
│   │   └── fasterrcnn_best.onnx
│   ├── pyproject.toml          # uv — replaces requirements.txt
│   ├── uv.lock
│   ├── Dockerfile.api
│   └── Dockerfile.worker
├── k8s/                        # Kubernetes manifests
│   ├── fastapi-deployment.yaml
│   ├── celery-worker-deployment.yaml
│   ├── redis-deployment.yaml
│   └── nextjs-deployment.yaml
└── .github/workflows/
    └── deploy.yaml
```

## 7. Implementation Phases

### Phase 1: Foundation Setup

- [ ]  Create a Supabase project (Auth, Database, Storage)
- [ ]  Create `profiles`, `videos`, `violations` tables + RLS policies
- [ ]  Set up monorepo, basic folder structure

### Phase 2: Backend Inference

- [ ]  Convert all 3 models to ONNX format (offline, one-time)
    - YOLO/RT-DETR: `model.export(format="onnx")` via ultralytics
    - Faster R-CNN: `torch.onnx.export(...)` via torchvision
- [ ]  Write output-normalization wrappers for the 3 ONNX models (using `onnxruntime`)
- [ ]  Implement shared IoU-tracker (for Faster R-CNN; YOLO/RT-DETR use built-in ByteTrack)
- [ ]  Implement `violation_logic.py` (association + decision)
- [ ]  Test logic on a sample video, output annotated violation images

### Phase 3: API & Auth

- [ ]  FastAPI endpoints `/videos/upload`, `/violations`, `/ws/camera`
- [ ]  Middleware to verify Supabase JWT
- [ ]  Integrate Celery + Redis for async video upload processing
- [ ]  Save violation images to Supabase Storage, metadata to Postgres

### Phase 4: Frontend

- [ ]  Login/signup page (Supabase Auth)
- [ ]  Video upload page with model selection
- [ ]  Real-time camera page (WebSocket + live bounding box display)
- [ ]  Violations dashboard (Supabase Realtime subscription)

### Phase 5: Containerization & Deployment

- [ ]  Write `Dockerfile.api` (FastAPI only, no ML deps — uses `uv`)
- [ ]  Write `Dockerfile.worker` (ONNX Runtime inference — uses `uv`, no torch needed)
- [ ]  Write Kubernetes manifests (Deployment, Service)
- [ ]  Create GKE cluster on GCP, deploy Redis + FastAPI + Celery worker
- [ ]  Deploy Next.js (Vercel or GKE)
- [ ]  Set up GitHub Actions: build → push to Artifact Registry → deploy to GKE

### Phase 6: Testing & Demo

- [ ]  End-to-end test: upload video → view results → check dashboard
- [ ]  Test real-time camera mode
- [ ]  Measure FPS/accuracy of the 3 models for comparison (for the report)
- [ ]  Prepare demo and write report

## 8. Cost & Operational Notes

- **GCP $300 trial**: used for GKE (FastAPI, Celery worker, Redis) — sufficient for several months if not running 24/7
- **Supabase free tier**: fully replaces self-hosted PostgreSQL and MinIO; covers DB + Auth + Storage (1GB) + Realtime. Project auto-pauses after 1 week of inactivity → unpause before demos if left idle
- **ONNX models**: `Dockerfile.worker` only needs `onnxruntime` (~50MB) instead of `torch` (~2GB) — significantly smaller image, faster pull times on GKE
- **uv**: used in both `Dockerfile.api` and `Dockerfile.worker` via `uv sync --frozen --no-dev` — faster than pip, no `requirements.txt`
- **Heavy models (Faster R-CNN, RT-DETR)**: if running on CPU, reduce input resolution and infer every N frames to keep real-time performance acceptable