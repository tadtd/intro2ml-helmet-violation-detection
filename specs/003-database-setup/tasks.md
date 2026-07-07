# Tasks: Database Setup

**Input**: Design documents from `/specs/003-database-setup/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create testing directory `tests/db/` for pgTAP tests.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Link local repository to Supabase cloud testing project `helmet-violation-test` via `supabase link`
- [x] T003 Create `profiles` table migration in `supabase/migrations/20260706000001_fr012_profiles_table.sql`

**Checkpoint**: Foundation ready - cloud project linked and root `profiles` table exists.

---

## Phase 3: User Story 1 - Video Processing Lifecycle (Priority: P1) 🎯 MVP

**Goal**: Extend the videos table with operational fields (progress_pct, status, error_message, processed_at) and model validation constraint.

**Independent Test**: pgTAP tests for table shape and check constraints on the videos table.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T004 [P] [US1] Create pgTAP test for videos schema shape and constraints in `tests/db/test_schema.sql`

### Implementation for User Story 1

- [x] T005 [US1] Create `videos` table migration in `supabase/migrations/20260706000002_fr013_fr014_videos_table.sql`

**Checkpoint**: At this point, the videos table and its model constraints are verifiable in PostgreSQL.

---

## Phase 4: User Story 2 - Role-Based Data Separation via RLS (Priority: P2)

**Goal**: Restrict operator queries to their own videos and violations, while admins and backend services bypass this restriction.

**Independent Test**: pgTAP tests authenticating as different roles and asserting visibility of rows.

### Tests for User Story 2

- [x] T006 [P] [US2] Create pgTAP test for operator/admin/service_role RLS access split in `tests/db/test_rls.sql`

### Implementation for User Story 2

- [x] T007 [US2] Create RLS policies migration for `profiles` and `videos` in `supabase/migrations/20260706000005_fr018_rls_policies.sql`

**Checkpoint**: At this point, Row Level Security is active and correctly enforcing the access split.

---

## Phase 5: User Story 3 - Violation Manual Review Workflow (Priority: P3)

**Goal**: Extend the violations table with confidence scoring, reviewer attribution, and manual review verdicts. Implement performance indexes.

**Independent Test**: pgTAP tests for violations schema constraints.

### Tests for User Story 3

- [x] T008 [P] [US3] Update pgTAP test suite with violations table validation in `tests/db/test_schema.sql`

### Implementation for User Story 3

- [x] T009 [US3] Create `violations` table migration in `supabase/migrations/20260706000003_fr015_fr016_violations_table.sql`
- [x] T010 [US3] Create indexes migration for performance in `supabase/migrations/20260706000004_fr017_indexes.sql`
- [x] T011 [US3] Append RLS policies for `violations` table to `supabase/migrations/20260706000005_fr018_rls_policies.sql`

**Checkpoint**: All three tables exist, have RLS applied, and performance indexes are defined.

---

## Phase 6: User Story 4 - Evidence Crop Access and Raw Video Expiration (Priority: P4)

**Goal**: Create private storage buckets for videos and violations. Implement signed URL generation for access and Celery beat periodic task for raw video expiration.

**Independent Test**: Manual setup verification or basic bucket existence assertion. Test the helper function and Celery task locally.

### Implementation for User Story 4

- [x] T012 [US4] Create storage buckets migration in `supabase/migrations/20260706000006_fr019_fr020_storage_buckets.sql`
- [x] T013 [US4] Add backend API helper function for generating Supabase `createSignedUrl` in `src/services/storage.py` (FR-021)
- [x] T014 [US4] Update Celery beat periodic task for deleting videos > 3 days old in `src/workers/cleanup.py` to explicitly exclude videos where `status = 'processing'` (FR-022)
- [x] T015 [US4] Create storage API helper to enforce path conventions (`user_id/video_id/filename` and `video_id/violation_id/cropname`) during uploads in `src/services/storage.py` (FR-020)

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validation and completion of the DB setup.

- [x] T016 Push migrations to the linked Supabase project using `supabase db push` and verify clean state via `supabase db reset --linked`.
- [x] T017 Run validation steps in `quickstart.md` to ensure all pgTAP tests pass against the remote Supabase testing instance using `pg_prove`.
- [x] T018 Create a data-seeding script `tests/db/seed_10k.sql` and run `EXPLAIN ANALYZE` to verify <2s query latency on `violations` filtering to satisfy SC-005.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories should proceed sequentially in priority order since later migrations (like RLS or indexes) depend on earlier tables existing.

### Parallel Opportunities

- Tests (T004, T006, T008) can be written in parallel before the migrations are authored.

## Implementation Strategy

### Incremental Delivery

1. Complete Setup + Foundational → Link test project and create `profiles` migration.
2. Add User Story 1 (Videos table) → Verify via remote pgTAP tests.
3. Add User Story 2 (RLS split) → Verify RLS via remote pgTAP tests.
4. Add User Story 3 (Violations table) → Verify schemas.
5. Add User Story 4 (Buckets).
6. Validate full suite via `supabase db push` and remote `pg_prove`.
