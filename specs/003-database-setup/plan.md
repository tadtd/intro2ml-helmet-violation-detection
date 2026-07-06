# Implementation Plan: Database Setup

**Branch**: `003-database-setup` | **Date**: 2026-07-06 | **Spec**: [spec.md](file:///C:/Users/HP/intro2ml-helmet-violation-detection/specs/003-database-setup/spec.md)

**Input**: Feature specification from `/specs/003-database-setup/spec.md`

## Summary

This plan outlines the extension of the `profiles`, `videos`, and `violations` schema on Supabase Postgres. It includes adding new operational and tracking columns, check constraints for model validation, performance indexes, Row Level Security (RLS) policies for role-based access control, and defining the two storage buckets (`videos` and `violations`). The implementation will be driven by pgTAP unit testing against a local Postgres instance using a local shim for Supabase-specific functions.

## Technical Context

**Language/Version**: SQL (PostgreSQL 15+)

**Primary Dependencies**: Supabase Postgres, pgTAP

**Storage**: PostgreSQL Database, Supabase Storage (Buckets)

**Testing**: pgTAP (Unit testing for schema shape, check constraints, indexes, and RLS)

**Target Platform**: Supabase Platform / Local Postgres

**Project Type**: Database Schema & Migration

**Performance Goals**: <2s query latency on 10k violation records (SC-005) (Scoped out of unit tests)

**Constraints**: RLS must strictly isolate operator data while allowing admin/service_role bypass (SC-006).

**Scale/Scope**: 3 core tables, 2 storage buckets, RLS policies.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle II (Comprehensive Testing Discipline)**: The plan adheres to using mock interfaces for external services. By implementing a minimal local shim for `auth.users`, `auth.uid()`, and `storage.*` objects, the migration and RLS policies can be tested against a plain, local Postgres instance using pgTAP without requiring a live Supabase project.
- **Principle V (Rigorous Data Governance)**: The plan defines the necessary tables and buckets to store high-fidelity image crops (`violations` bucket) and log detection details transactionally.

*Status: PASS*

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
    ├── shim.sql               # Minimal local shim for Supabase auth/storage
    ├── test_schema.sql        # pgTAP tests for tables, columns, constraints, and indexes
    └── test_rls.sql           # pgTAP tests for operator/admin/service_role access
```

**Structure Decision**: Migrations are split per Functional Requirement (FR-012 through FR-020) to provide a clear, linear progression of schema changes. Tests are located in a dedicated `tests/db/` directory, structured to separate the shim environment from actual schema and RLS test logic. 
*Note on FR-021 & FR-022*: FR-021 (Signed URLs) does not require a migration; it will be implemented as a backend API helper calling Supabase's `createSignedUrl`. FR-022 (Storage Expiration) will be implemented as a Celery beat periodic task (utilizing the existing worker infrastructure) rather than `pg_cron` to avoid introducing new Postgres extensions.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations.*
