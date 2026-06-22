# Helmet Violation Detection — PLAN.md

## 1. Goal

Build a web system for detecting motorcycle helmet violations from uploaded
videos and live camera streams. The system supports model comparison across
YOLO, RT-DETR, and Faster R-CNN, stores violation evidence, and exposes a
dashboard for operators and admins.

## 2. Repository Structure

```text
intro2ml-helmet-violation-detection/
├── README.md
├── PLAN.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── README.md
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── Dockerfile.api
│   ├── Dockerfile.worker
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── auth.py
│   │   ├── celery_app.py
│   │   ├── tasks.py
│   │   ├── tracker.py
│   │   ├── violation_logic.py
│   │   ├── db/
│   │   │   ├── client.py
│   │   │   ├── profiles.py
│   │   │   ├── storage.py
│   │   │   ├── videos.py
│   │   │   └── violations.py
│   │   ├── models/
│   │   │   ├── base.py
│   │   │   ├── yolo_wrapper.py
│   │   │   ├── rtdetr_wrapper.py
│   │   │   └── fasterrcnn_wrapper.py
│   │   ├── routes/
│   │   │   ├── camera.py
│   │   │   ├── videos.py
│   │   │   └── violations.py
│   │   └── weights/
│   │       └── README.md
│   └── supabase/
│       └── schema/
│           ├── 01_profiles.sql
│           ├── 02_videos.sql
│           └── 03_violations.sql
├── frontend/
│   ├── package.json
│   ├── next.config.ts
│   ├── Dockerfile
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── globals.css
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── (app)/
│   │       ├── layout.tsx
│   │       ├── dashboard/
│   │       │   └── page.tsx
│   │       ├── upload/
│   │       │   └── page.tsx
│   │       └── camera/
│   │           └── page.tsx
│   └── utils/
│       └── supabase/
│           ├── client.ts
│           ├── server.ts
│           └── middleware.ts
├── models/
│   ├── pyproject.toml
│   ├── train_yolo.py
│   ├── train_rtdetr.py
│   ├── train_fasterrcnn.py
│   ├── dataset.py
│   ├── metrics.py
│   ├── plots.py
│   ├── raytune.py
│   └── checkpoints/
│       ├── README.md
│       └── convert2onnx.py
├── crawl/
│   ├── README.md
│   └── scripts/
│       ├── build_unified_coco_dataset.py
│       ├── merge_cvat_coco_back.py
│       └── prepare_cvat_coco_task.py
├── data/
├── docs/
├── report/
└── k8s/
```

## 3. Architecture

```text
Next.js frontend
  ├── Supabase Auth — login and session management
  ├── Upload page — sends authenticated video + model choice to FastAPI
  ├── Dashboard — reads violations via REST, subscribes to Supabase Realtime
  └── Camera page — streams frames to FastAPI WebSocket, draws live boxes

FastAPI backend
  ├── Verifies Supabase JWTs on every request
  ├── POST /videos/upload — saves video to Supabase Storage, enqueues Celery task
  ├── GET  /violations   — paginated query, RLS-filtered per user role
  └── WS   /ws/camera   — per-frame inference, saves realtime violations

Celery worker
  ├── Downloads video from Supabase Storage
  ├── Runs frame-by-frame inference with selected ONNX model
  ├── Tracks motorbikes, associates non-helmet detections
  ├── Uploads violation crops to Supabase Storage (violations bucket)
  └── Writes violation rows and updates video status in Postgres

Supabase
  ├── Auth     — user sessions and JWTs
  ├── Postgres — profiles, videos, violations
  ├── Storage  — buckets: `videos` (originals), `violations` (crops)
  └── Realtime — dashboard live updates on violation inserts
```

## 4. Technology Stack

| Area | Choice |
|---|---|
| Frontend | Next.js, React, Supabase SSR/client SDK |
| Backend API | FastAPI |
| Async jobs | Celery + Redis |
| ML runtime | ONNX Runtime + OpenCV |
| Database | Supabase Postgres |
| Auth | Supabase Auth |
| Storage | Supabase Storage (`videos`, `violations` buckets) |
| Package managers | `uv` (Python), `npm` (frontend) |
| Local orchestration | Docker Compose |
| Deployment | GKE (after local E2E is stable) |

## 5. Data Model

Run schema files from `backend/supabase/schema/` in numeric order.

### `profiles`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | FK → `auth.users`, primary key |
| `role` | text | `admin` or `operator`, default `operator` |
| `full_name` | text | optional display name |

### `videos`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | generated, primary key |
| `user_id` | uuid | FK → `auth.users` |
| `filename` | text | original upload name |
| `storage_path` | text | path inside `videos` bucket |
| `content_type` | text | upload MIME type |
| `model_used` | text | `yolo`, `rtdetr`, or `fasterrcnn` |
| `status` | text | `pending` → `processing` → `done` / `failed` |
| `created_at` | timestamptz | auto |

### `violations`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | generated, primary key |
| `video_id` | uuid | nullable — null means live camera detection |
| `user_id` | uuid | FK → `auth.users` |
| `track_id` | int | tracked motorbike ID, nullable |
| `model_used` | text | model that produced the detection |
| `image_url` | text | public URL of the violation crop |
| `timestamp` | timestamptz | detection time, auto |

### RLS Policies
- Operators read only their own rows (`auth.uid() = user_id`)
- Admins read all rows (join to `profiles` where `role = 'admin'`)
- Backend uses `SERVICE_ROLE_KEY` and bypasses RLS for writes

## 6. Detection Pipeline

All model wrappers normalize outputs into a shared `Detection` dataclass:

```python
@dataclass
class Detection:
    class_name: str        # "motorbike" | "helmet" | "non-helmet"
    box: tuple             # (x1, y1, x2, y2)
    confidence: float
    track_id: int | None   # assigned after tracking step
```

Pipeline steps per video:

1. Download video from Supabase Storage to worker `/tmp/`
2. Decode frames with OpenCV (`cv2.VideoCapture`)
3. Run selected ONNX model wrapper → list of `Detection`
4. Track motorbikes across frames (`IoUTracker` or ByteTrack)
5. Associate `non-helmet` boxes with nearest motorbike box
6. Deduplicate — one crop saved per `track_id` per violation window
7. Upload crop to `violations` bucket → get public URL
8. Insert violation row into Postgres
9. Update video `status` → `done` or `failed`
10. Delete `/tmp/` video file

## 7. Module Responsibilities

### `app/db/`
Leaf module — no imports from routes, tasks, or auth.

| File | Responsibility |
|---|---|
| `client.py` | Supabase singleton using `SERVICE_ROLE_KEY` |
| `videos.py` | `insert_video`, `update_video_status`, `get_video` |
| `violations.py` | `insert_violation`, `list_violations` |
| `storage.py` | `upload_file`, `download_file`, `get_public_url`, `delete_file` |
| `profiles.py` | `get_profile`, `upsert_profile` |

### `app/models/`
| File | Responsibility |
|---|---|
| `base.py` | `BaseDetector` ABC, `Detection` dataclass |
| `yolo_wrapper.py` | ONNX pre/postprocess for YOLO |
| `rtdetr_wrapper.py` | ONNX pre/postprocess for RT-DETR |
| `fasterrcnn_wrapper.py` | ONNX pre/postprocess for Faster R-CNN |

### `app/routes/`
| File | Endpoints |
|---|---|
| `videos.py` | `POST /videos/upload`, `GET /videos/{id}` |
| `violations.py` | `GET /violations` |
| `camera.py` | `WS /ws/camera` |

### Other backend modules
| File | Responsibility |
|---|---|
| `auth.py` | `get_current_user` FastAPI dependency (JWT verify) |
| `tracker.py` | `IoUTracker` — motorbike tracking across frames |
| `violation_logic.py` | `find_violations` — association + deduplication |
| `tasks.py` | `process_video` Celery task |
| `celery_app.py` | Celery app factory |
| `config.py` | Pydantic `Settings` from env vars |

## 8. Environment Variables

Backend (`.env`):
```text
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=
SUPABASE_VIDEO_BUCKET=videos
SUPABASE_VIOLATIONS_BUCKET=violations
REDIS_URL=redis://localhost:6379/0
```

Frontend (`.env.local`):
```text
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 9. Local Development

Backend API:
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Celery worker:
```bash
cd backend
uv run celery -A app.celery_app.celery_app worker --loglevel=info
```

All services via Docker Compose:
```bash
docker compose up --build
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## 10. Milestones

### Milestone 1 — Local Baseline ✅ (mostly done)
- [x] FastAPI app, auth dependency, routes, health endpoint
- [x] Supabase schema SQL modules
- [x] Next.js login, upload, dashboard, camera pages
- [x] Docker Compose for Redis, API, worker
- [x] Video upload to Supabase Storage before enqueueing
- [ ] Smoke-test instructions for running all services locally together

### Milestone 2 — Backend Processing
- [ ] `storage.py`: `download_file` helper for worker to fetch queued videos
- [ ] `tasks.py`: full `process_video` with status transitions and error handling
- [ ] Frame sampling strategy (every N frames, configurable)
- [ ] YOLO ONNX output parsing (exact tensor shapes from export)
- [ ] RT-DETR ONNX output parsing
- [ ] Faster R-CNN ONNX output parsing
- [ ] Deduplication: one crop per `track_id` per violation window
- [ ] Unit tests for `IoUTracker` and `find_violations`

### Milestone 3 — Frontend Workflows
- [ ] Video status polling on upload page (`pending` → `processing` → `done`)
- [ ] Upload error states with user-facing messages
- [ ] Violation images rendered inline on dashboard (not just URLs)
- [ ] Authenticated REST fallback if Realtime subscription drops
- [ ] Camera page: frame capture loop → WebSocket send
- [ ] Camera page: draw bounding boxes over live preview canvas

### Milestone 4 — Supabase Hardening
- [ ] Create `videos` and `violations` storage buckets with correct policies
- [ ] Decide visibility: `videos` bucket private, `violations` bucket public
- [ ] Add indexes: `videos.user_id`, `violations.user_id`, `violations.timestamp`
- [ ] Add insert/update RLS policies if any client-side writes are needed
- [ ] Document schema migration steps for future changes

### Milestone 5 — Model Evaluation
- [ ] Export YOLO, RT-DETR, Faster R-CNN to ONNX (final weights)
- [ ] Record tensor shapes for each model's ONNX output
- [ ] Evaluate FPS, precision, recall, mAP on shared validation split
- [ ] Document hardware and inference settings used
- [ ] Pick default demo model based on accuracy/speed tradeoff

### Milestone 6 — Deployment
- [ ] Finalize `Dockerfile.api` and `Dockerfile.worker` for production
- [ ] Frontend deployment (Vercel or GKE)
- [ ] Kubernetes manifests in `k8s/` (FastAPI, worker, Redis, optional Next.js)
- [ ] Secrets via platform secret manager — no committed `.env` files
- [ ] GitHub Actions: lint → build images → push → deploy to GKE

## 11. Immediate Next Steps

1. Create `videos` and `violations` buckets in Supabase Storage
2. Implement `download_file` in `app/db/storage.py`
3. Implement full `process_video` task in `app/tasks.py`
4. Export ONNX models and record output tensor shapes
5. Complete ONNX output parsing in all three wrappers
6. Run end-to-end: upload video → worker processes → dashboard shows violation