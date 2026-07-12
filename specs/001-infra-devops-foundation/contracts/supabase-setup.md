# Contract: Supabase Setup

## Schema Order

Run SQL modules from `backend/supabase/schema/` in this exact order:

1. `01_profiles.sql`
2. `02_videos.sql`
3. `03_violations.sql`
4. `04_indexes.sql`
5. `05_realtime.sql`

## Required Tables

| Table | Required Purpose | Verification |
|-------|------------------|--------------|
| `profiles` | User role data | Table exists with RLS enabled |
| `videos` | Uploaded video metadata | Table exists with RLS enabled |
| `violations` | Violation evidence metadata | Table exists with RLS enabled |

## Required Bucket Policies

| Bucket | Visibility | Writer | Reader |
|--------|------------|--------|--------|
| `videos` | Private | API/worker service context | API/worker service context |
| `violations` | Public-read | API/worker service context | Dashboard/public image URL consumers |

## Access Contract

- Frontend uses anon/publishable credentials for auth/session behavior only.
- API and worker use service-role credentials for storage and database writes.
- Service-role credentials are supplied by untracked local `.env` or external
  secret references only.

## Realtime Contract

- Violation inserts must be eligible for realtime subscription by the dashboard
  after schema setup.
- Setup documentation must include a verification step for realtime enablement.
