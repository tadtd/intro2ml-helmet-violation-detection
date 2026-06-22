# Helmet Violation Detection

Monorepo for a helmet violation detection system using Next.js, FastAPI, Celery,
Redis, Supabase, and ONNX Runtime.

## Setup

1. Create a Supabase project and run `backend/supabase_schema.sql` in the SQL
   editor.
2. Copy `.env.example` to `.env` and fill Supabase values.
3. Start Redis, API, and worker:

```powershell
docker compose up --build
```

4. Start the frontend:

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:3000`; the API runs at
`http://localhost:8000`.

## Model Weights

Place exported ONNX files in `backend/app/weights/`:

- `yolo_best.onnx`
- `rtdetr_best.onnx`
- `fasterrcnn_best.onnx`

The wrapper classes are wired for ONNX Runtime, but final output parsing depends
on the exported model tensor shape and class mapping.
