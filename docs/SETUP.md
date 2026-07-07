# How to properly setup

- Below are the parts you need to setup in order to run this project.

## AI Coding tools and prompt engineering
This project is configured with **Speckit** AI agent tooling (located in the `.agents` and `.specify` folders). 
- **Agent Instructions:** The AI assistant will automatically consult `AGENTS.md` and `PLAN.md` for project context.
- **Agent Skills:** AI assistants can use structured skills (like `speckit-plan`, `speckit-tasks`, and `speckit-implement`) to systematically plan and write code.

## Docker
Docker Compose is the fastest way to run all backend services (FastAPI, Celery worker, and Redis) locally without installing dependencies individually.
- Ensure you have Docker installed and running.
- From the root directory, run:
  ```bash
  docker compose up --build
  ```

## Database (Supabase)
This project uses **Supabase** for PostgreSQL, Authentication, and Storage.
1. Create a project on Supabase and retrieve your API keys.
2. **Schema Setup:** Run the SQL scripts found in `backend/supabase/schema/` in numeric order (`01_profiles.sql`, `02_videos.sql`, `03_violations.sql`) in your Supabase SQL editor.
3. **Storage Setup:** Create two buckets in Supabase Storage: `videos` (private) and `violations` (public).

## Backend (FastAPI & Celery)
The backend uses Python and the `uv` package manager.
1. Copy `.env.example` to `.env` in the root directory and fill in your Supabase and Redis credentials.
2. Install dependencies:
   ```bash
   cd backend
   uv sync
   ```
3. Run the FastAPI server:
   ```bash
   uv run uvicorn app.main:app --reload
   ```
4. *Optional (If not using Docker):* Run the Celery worker in a separate terminal:
   ```bash
   uv run celery -A app.celery_app.celery_app worker --loglevel=info
   ```

## Frontend (Next.js)
The frontend is a Next.js application.
1. Inside the `frontend/` directory, create a `.env.local` file with the following:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your_supabase_anon_key
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   ```
2. Install dependencies and start the development server:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```