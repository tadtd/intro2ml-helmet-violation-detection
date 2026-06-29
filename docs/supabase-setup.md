# Supabase Development Setup

This runbook configures a Supabase development project for the existing Helmet
Violation Detection monorepo. Use local development projects only, and keep real
credentials in an untracked `.env` file or in your shell.

## Prerequisites

- Supabase development project access.
- Repository checked out locally.
- PowerShell from the repository root.
- `.env.example` copied to untracked `.env` and filled with local values.

```powershell
Copy-Item .env.example .env
notepad .env
```

Do not commit `.env`, service-role keys, tokens, kubeconfigs, certificates, or
private keys.

## Required Local Values

| Variable | Consumer | Notes |
|----------|----------|-------|
| `SUPABASE_URL` | API, worker | Development project URL. |
| `SUPABASE_ANON_KEY` | API auth/JWT support | Anon key only. |
| `SUPABASE_SERVICE_ROLE_KEY` | API, worker | Backend-only service credential. |
| `SUPABASE_JWT_SECRET` | API | JWT verification secret from the development project. |
| `SUPABASE_VIDEO_BUCKET` | API, worker | Use `videos`. |
| `SUPABASE_STORAGE_BUCKET` | API, worker | Use `violations`. |
| `NEXT_PUBLIC_SUPABASE_URL` | frontend | Frontend-safe project URL. |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | frontend | Publishable or anon key only. |
| `NEXT_PUBLIC_API_BASE_URL` | frontend | `http://localhost:8000` for local runs. |
| `REDIS_URL` | API, worker | `redis://localhost:6379/0` for host runs; Compose overrides to `redis://redis:6379/0`. |

Frontend-facing values must not contain service-role credentials. API and worker
contexts are the only places that may use the service-role key.

## Schema Order

Run the SQL files in `backend/supabase/schema/` from the Supabase SQL editor in
this exact order:

1. `01_profiles.sql`
2. `02_videos.sql`
3. `03_violations.sql`
4. `04_indexes.sql`
5. `05_realtime.sql`

The new `04_indexes.sql` and `05_realtime.sql` files are additive. They use
idempotent guards where PostgreSQL supports them and do not drop existing data.

## Table Verification

After the schema files run, verify the following tables exist in the `public`
schema and have Row Level Security enabled:

| Table | Expected purpose | Verification |
|-------|------------------|--------------|
| `profiles` | User role data | RLS enabled; select policy lets users read their own profile. |
| `videos` | Uploaded source video metadata | RLS enabled; owner/admin select policy exists. |
| `violations` | Violation evidence metadata | RLS enabled; owner/admin select policy exists. |

Use the Supabase dashboard table editor or SQL editor to confirm each table is
present. If a table already exists, rerunning the numbered modules should leave
existing rows intact.

## Storage Buckets

Create or verify these Supabase Storage buckets:

| Bucket | Visibility | Purpose |
|--------|------------|---------|
| `videos` | Private | Original uploaded videos used by the API and worker. |
| `violations` | Public-read | Evidence crop images that may be shown through public URLs. |

The API and worker write to both buckets using backend service-role credentials.
Frontend code must not write with a service-role key.

Verification:

1. Confirm `videos` exists and is not public.
2. Confirm `violations` exists and can serve public evidence URLs.
3. After the local upload smoke test, confirm a matching object appears in the
   private `videos` bucket.

## Auth Setup

Create development users through Supabase Auth for team testing. The schema
supports `operator` and `admin` roles in `profiles.role`.

Expected behavior:

- Operators can read their own profile, video rows, and violation rows.
- Admins can read video and violation rows across users through the documented
  policies.
- Backend API and worker code perform trusted storage/database writes with the
  service-role key from local environment only.

## Realtime Setup

`05_realtime.sql` adds `public.violations` to the `supabase_realtime`
publication when the publication exists and the table is not already included.
It also sets replica identity to `full` for complete row payloads.

Verification options:

1. In Supabase, inspect the Realtime publication and confirm `violations` is
   included.
2. Subscribe to violation inserts from a local client using the anon key.
3. Insert a development violation row and confirm the subscriber receives the
   insert event.

## Rollback And Failure Notes

- If files are run out of order, stop and rerun from the first missing numbered
  file. Do not drop tables to recover unless you intentionally reset the
  development project.
- If a bucket already exists, verify its visibility instead of recreating it.
- If RLS is missing, rerun the owning table module and verify policies again.
- If realtime setup fails because the publication is absent, confirm Supabase
  Realtime is enabled for the project, then rerun `05_realtime.sql`.
- If an index migration fails, inspect the referenced table and column names
  before rerunning. Existing rows do not need to be deleted.
