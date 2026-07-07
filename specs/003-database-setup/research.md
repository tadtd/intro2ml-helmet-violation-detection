# Phase 0: Research & Technical Decisions

## Unit Testing Framework for Postgres

- **Decision**: Use `pgTAP` for database unit testing.
- **Rationale**: `pgTAP` allows tests to run directly against Postgres, enabling real execution of check constraints, schema shape validation, and Row Level Security (RLS) policies rather than mocking them at the application layer. This matches the strict unit testing requirements and ensures RLS policies correctly isolate operator/admin/service_role access before deployment.
- **Alternatives considered**: Python-based testing with `pytest` and a mocked database adapter, or Supabase Local CLI test runner. `pgTAP` was chosen for its direct SQL execution and explicit instruction from the user.

## Supabase Cloud Testing Environment

- **Decision**: Test directly against a dedicated Supabase cloud testing project (`helmet-violation-test`).
- **Rationale**: The previous approach of using a local `shim.sql` created maintenance overhead and couldn't perfectly replicate Supabase's internal schema behavior (auth.users, storage.objects). By using a dedicated test project, migrations can be pushed via `supabase db push`, pgTAP can be enabled natively via the Supabase Dashboard Extensions, and state isolation between test runs is guaranteed via `supabase db reset --linked`.
- **Alternatives considered**: Minimal local shim against vanilla Postgres (discarded due to user command), or local `supabase start` (discarded in favor of a cloud testing environment).

## Storage Lifecycle and Query Latency

- **Decision**: Explicitly scope out SC-005 (query latency) and SC-007 (storage lifecycle timing) from unit testing.
- **Rationale**: `pgTAP` is a unit testing framework for schema logic. Performance testing (SC-005) requires generating a 10,000-record dataset and profiling query plans, which is better suited for an integration testing environment. Storage lifecycle (SC-007) relies on Supabase Storage Cron/Workers which cannot be unit-tested via Postgres SQL.
- **Alternatives considered**: N/A - directly specified by user.
