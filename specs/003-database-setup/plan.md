# Implementation Plan: Database Setup

**Branch**: `003-database-setup` | **Date**: 2026-07-06 | **Spec**: [spec.md](file:///C:/Users/HP/intro2ml-helmet-violation-detection/specs/003-database-setup/spec.md)

**Input**: Feature specification from `/specs/003-database-setup/spec.md`

## Summary

This plan outlines the extension of the `profiles`, `videos`, and `violations` schema on Supabase Postgres. It includes adding new operational and tracking columns, check constraints for model validation, performance indexes, Row Level Security (RLS) policies for role-based access control, and defining the two storage buckets (`videos` and `violations`). 

**Testing Approach Override**: Instead of local mocked shims, the implementation will be tested directly against a dedicated Supabase cloud testing project (`helmet-violation-test`). Migrations will be applied using the Supabase CLI (`supabase link` and `supabase db push`). pgTAP will be enabled via the Supabase Dashboard Extensions, and tests will be run via `pg_prove` connecting to the remote testing connection string. Clean state between test runs will be maintained using `supabase db reset --linked`.

## Technical Context

**Language/Version**: SQL (PostgreSQL 15+)

**Primary Dependencies**: Supabase Postgres, pgTAP

**Storage**: PostgreSQL Database, Supabase Storage (Buckets)

**Testing**: pgTAP (Unit testing for schema shape, check constraints, indexes, and RLS) executed via `pg_prove` against remote connection string.

**Target Platform**: Supabase Cloud Testing Project (`helmet-violation-test`)

**Project Type**: Database Schema & Migration

**Performance Goals**: <2s query latency on 10k violation records (SC-005) (Scoped out of unit tests)

**Constraints**: RLS must strictly isolate operator data while allowing admin/service_role bypass (SC-006).

**Scale/Scope**: 3 core tables, 2 storage buckets, RLS policies.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle II (Comprehensive Testing Discipline)**: **VIOLATION JUSTIFIED**. Principle II requires mock interfaces to prevent flaky live-service tests. However, the user explicitly commanded testing directly on a dedicated live Supabase cloud project (`helmet-violation-test`) using `supabase db reset --linked`. While this introduces network state dependencies, it allows authentic testing of Supabase-specific features (auth.users, RLS) without maintaining complex local shims.
- **Principle V (Rigorous Data Governance)**: The plan defines the necessary tables and buckets to store high-fidelity image crops (`violations` bucket) and log detection details transactionally.

*Status: PASS (with Justification)*

## Project Structure

### Documentation (this feature)

```text
specs/003-database-setup/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (to be generated later)
```

### Source Code (repository root)

```text
supabase/
└── migrations/
    ├── 20260706000001_fr012_profiles_table.sql
    ├── 20260706000002_fr013_fr014_videos_table.sql
    ├── 20260706000003_fr015_fr016_violations_table.sql
    ├── 20260706000004_fr017_indexes.sql
    ├── 20260706000005_fr018_rls_policies.sql
    └── 20260706000006_fr019_fr020_storage_buckets.sql

tests/
└── db/
    ├── test_schema.sql        # pgTAP tests for tables, columns, constraints, and indexes
    └── test_rls.sql           # pgTAP tests for operator/admin/service_role access
```

**Structure Decision**: Migrations are split per Functional Requirement (FR-012 through FR-020) to provide a clear, linear progression of schema changes. Tests are located in a dedicated `tests/db/` directory. The previous `shim.sql` has been removed, as the testing environment is now a true Supabase cloud instance.
*Note on FR-021 & FR-022*: FR-021 (Signed URLs) does not require a migration; it will be implemented as a backend API helper calling Supabase's `createSignedUrl`. FR-022 (Storage Expiration) will be implemented as a Celery beat periodic task (utilizing the existing worker infrastructure) rather than `pg_cron` to avoid introducing new Postgres extensions.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

- **Violation**: Principle II (Live Testing)
- **Justification**: Explicitly commanded by user to use `helmet-violation-test` cloud project to avoid the maintenance burden of local mock shims for Supabase internals. Clean state is maintained via `supabase db reset --linked`.
