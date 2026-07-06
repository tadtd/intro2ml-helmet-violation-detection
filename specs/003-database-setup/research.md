# Phase 0: Research & Technical Decisions

## Unit Testing Framework for Postgres

- **Decision**: Use `pgTAP` for database unit testing.
- **Rationale**: `pgTAP` allows tests to run directly against Postgres, enabling real execution of check constraints, schema shape validation, and Row Level Security (RLS) policies rather than mocking them at the application layer. This matches the strict unit testing requirements and ensures RLS policies correctly isolate operator/admin/service_role access before deployment.
- **Alternatives considered**: Python-based testing with `pytest` and a mocked database adapter, or Supabase Local CLI test runner. `pgTAP` was chosen for its direct SQL execution and explicit instruction from the user.

## Supabase Local Testing Shim

- **Decision**: Create a minimal local shim for `auth.users`, `auth.uid()`, `storage.buckets`, and `storage.objects`.
- **Rationale**: Supabase relies heavily on its internal `auth` and `storage` schemas which are not present in a vanilla Postgres instance by default. To test the migrations and RLS policies locally using `pgTAP` without spinning up a full Supabase project container stack, a lightweight shim mimicking these schemas and functions is required.
- **Alternatives considered**: Spinning up the full Supabase local development environment via `supabase start`. This was rejected because the requirement explicitly requested a minimal local shim against plain Postgres for fast, isolated unit tests.

## Storage Lifecycle and Query Latency

- **Decision**: Explicitly scope out SC-005 (query latency) and SC-007 (storage lifecycle timing) from unit testing.
- **Rationale**: `pgTAP` is a unit testing framework for schema logic. Performance testing (SC-005) requires generating a 10,000-record dataset and profiling query plans, which is better suited for an integration testing environment. Storage lifecycle (SC-007) relies on Supabase Storage Cron/Workers which cannot be unit-tested via Postgres SQL.
- **Alternatives considered**: N/A - directly specified by user.
