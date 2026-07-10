# Supabase Database

This folder is the single source of truth for database structure and database test SQL.

```text
supabase/
+-- migrations/   # Applied by `npx supabase db push`
+-- tests/        # pgTAP tests, local test shim, and benchmark seed SQL
```

## Apply Schema

From the repository root:

```powershell
npx supabase db push
```

## Run SQL Tests Manually

Against a database with pgTAP available:

```powershell
psql $env:DB_URL -f supabase/tests/shim.sql
psql $env:DB_URL -f supabase/tests/test_schema.sql
psql $env:DB_URL -f supabase/tests/test_rls.sql
```

## Benchmark Seed

```powershell
psql $env:DB_URL -f supabase/tests/seed_10k.sql
```