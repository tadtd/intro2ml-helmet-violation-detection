# Quickstart & Validation Guide

## Prerequisites
- PostgreSQL 15+ installed locally (or via Docker)
- `pgTAP` extension installed in the Postgres instance

## Setting Up the Test Environment

1. Create a local test database:
   ```bash
   createdb helmet_violation_test
   ```

2. Install `pgTAP`:
   ```bash
   psql -d helmet_violation_test -c "CREATE EXTENSION IF NOT EXISTS pgtap;"
   ```

3. Load the Supabase shim (which creates `auth.users`, `storage.buckets`, etc.):
   ```bash
   psql -d helmet_violation_test -f tests/db/shim.sql
   ```

4. Apply the migrations in sequence:
   ```bash
   psql -d helmet_violation_test -f supabase/migrations/20260706000001_fr012_profiles_table.sql
   psql -d helmet_violation_test -f supabase/migrations/20260706000002_fr013_fr014_videos_table.sql
   psql -d helmet_violation_test -f supabase/migrations/20260706000003_fr015_fr016_violations_table.sql
   psql -d helmet_violation_test -f supabase/migrations/20260706000004_fr017_indexes.sql
   psql -d helmet_violation_test -f supabase/migrations/20260706000005_fr018_rls_policies.sql
   psql -d helmet_violation_test -f supabase/migrations/20260706000006_fr019_fr020_storage_buckets.sql
   ```

## Running the Unit Tests

Execute the pgTAP test suite to validate schema shape, constraints, and RLS behavior:

```bash
pg_prove -d helmet_violation_test tests/db/test_schema.sql
pg_prove -d helmet_violation_test tests/db/test_rls.sql
```

**Expected Outcome**: All `pgTAP` tests should report `PASS`, confirming that the check constraints (e.g. `model_used` IN ('YOLO', ...)), indexes, and RLS operator/admin isolation policies work exactly as designed.
