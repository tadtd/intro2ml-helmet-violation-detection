# Feature Specification: Supabase Database and Storage Setup

**Feature Branch**: `003-database-setup`

**Created**: 2026-07-05

**Status**: Draft

**Input**: User description: "Set up database for me, the database setup extends the existing three-table schema (profiles, videos, violations) on Supabase Postgres, with Supabase Storage handling binary assets, and Row Level Security enforcing the operator/admin access split required by FR-010. The profiles table remains a thin extension of auth.users, storing role (admin or operator) and display name. The videos table gains a few operational fields beyond what exists today: an error_message and progress_pct to support the pending/processing/done/failed lifecycle described in the user stories, and a processed_at timestamp for auditing; model_used stays constrained to the three supported models (YOLO, RT-DETR, Faster R-CNN) via a check constraint. The violations table is extended with a confidence score (needed for filtering and prioritizing review, per FR-005 and SC-005), and a review workflow of reviewed, reviewer_id, and verdict (confirmed, false positive, or unclear) to support the manual approve/dismiss workflow described in User Story 3; video_id remains nullable to accommodate live-stream violations that aren't tied to an uploaded file. Indexes are added on the columns the dashboard queries most — user_id and status on videos, and user_id, reviewed, timestamp, and model_used on violations — to meet the sub-2-second filtering target on 10,000 records specified in SC-005. RLS policies are enabled on all three tables so operators can only read and update their own videos and violations, while admins bypass that restriction and see everything, matching the access model in User Story 3; backend services themselves (Ingestion, Inference Worker) write through the Supabase service-role key, which bypasses RLS entirely, since these policies exist to govern client-facing access only. On the storage side, two private buckets are created — videos for raw uploaded footage and violations for composite evidence crops — using a path convention keyed by user_id/video_id and video_id/violation_id respectively, with all client access mediated through backend-generated signed URLs rather than direct bucket exposure, since these images may contain identifiable people and vehicles. Finally, the retention policy set out in the spec applies at the storage layer: violation evidence crops and their database records are retained permanently, while raw video files in the videos bucket are automatically deleted after 3 days to keep storage costs bounded, implemented either as a Supabase Storage lifecycle rule or a scheduled cleanup task running alongside the existing Celery workers."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Video Processing Lifecycle & Progress Tracking (Priority: P1)
As a traffic officer (operator), I want to see the exact processing stage of my uploaded videos (transitioning through pending, processing, done, or failed), along with a progress percentage and descriptive error messages if a failure occurs, so that I have complete visibility over the automated analysis pipeline.

**Why this priority**: Highly critical for core workflow feedback. Standard uploads can take significant time to process, and operators need immediate, granular visual updates on progress and clean explanations if a file fails to process.

**Independent Test**: Can be tested by initiating a video analysis task, inspecting the database record's operational fields (`status`, `progress_pct`, `error_message`, and `processed_at`) at different intervals, and verifying they transition correctly.

**Acceptance Scenarios**:
1. **Given** an uploaded video file, **When** the ingest service creates the database record, **Then** `status` is set to `pending`, `progress_pct` is set to 0, and `error_message` is null.
2. **Given** a video starts processing, **When** the inference engine analyzes frames, **Then** `status` updates to `processing` and `progress_pct` updates dynamically.
3. **Given** a video finishes processing successfully, **When** the job completes, **Then** `status` updates to `done`, `progress_pct` is set to 100, and `processed_at` is populated with the completion timestamp.
4. **Given** a video processing job encounters an error (e.g. invalid codec), **When** the failure is caught, **Then** `status` updates to `failed` and `error_message` is written with a detailed user-friendly error description.

---

### User Story 2 - Role-Based Data Separation via RLS (Priority: P2)
As a traffic officer (operator), I want my dashboard queries to be restricted to my own uploaded videos and violations, while as an administrator, I want to see all videos and violations across the entire department, so that data access matches official operational privileges.

**Why this priority**: Required for data privacy and role division. Non-admin users must not access or edit data created by other operators.

**Independent Test**: Can be tested by logging into the application with an operator account, requesting videos and violations, and verifying that only records belonging to the logged-in user are returned. Then logging in as an admin and verifying that all records are returned.

**Acceptance Scenarios**:
1. **Given** an authenticated operator, **When** they list videos or violations, **Then** Row Level Security (RLS) restricts the returned rows to those matching their own profile ID.
2. **Given** an authenticated administrator, **When** they request videos or violations, **Then** RLS allows them to view all records in the system.
3. **Given** backend ingestion and inference workers writing to the database, **When** they connect using the service role, **Then** they bypass RLS restrictions entirely.

---

### User Story 3 - Violation Manual Review Workflow (Priority: P3)
As a traffic administrator or reviewer, I want to review logged violations, view the high-resolution evidence crops, and assign a review status (reviewed, reviewer, and verdict of confirmed, false positive, or unclear) so that we can audit the ML outputs before official citations are issued.

**Why this priority**: Critical for regulatory compliance and legal validity. Bounding box coordinates and class indexes must undergo human verification prior to fine generation.

**Independent Test**: Can be tested by querying pending violations, applying a review verdict, and verifying that the fields `reviewed`, `reviewer_id`, and `verdict` update correctly in the database.

**Acceptance Scenarios**:
1. **Given** a violation record, **When** an operator logs a new detection, **Then** `reviewed` defaults to false, and both `reviewer_id` and `verdict` are null.
2. **Given** a live-stream detection (not associated with an uploaded file), **When** the record is created, **Then** `video_id` is set to null, allowing the violation to exist independently.
3. **Given** a reviewer inspects a violation, **When** they mark it as confirmed or false positive, **Then** `reviewed` is set to true, `reviewer_id` points to the reviewer's profile, and `verdict` matches their action.

---

### User Story 4 - Evidence Crop Access and Raw Video Expiration (Priority: P4)
As a system administrator, I want raw uploaded video files to be deleted after 3 days to manage storage costs, while keeping cropped violation evidence images and their database logs permanently for auditing.

**Why this priority**: Cost optimization. High-resolution raw videos consume significant storage space, whereas evidence crop images are lightweight and required for permanent legal record keeping.

**Independent Test**: Can be tested by checking file existence in the `videos` bucket after 3 days to verify deletion, and checking the `violations` bucket to verify evidence crops and DB records remain permanently.

**Acceptance Scenarios**:
1. **Given** an uploaded raw video file in the private `videos` storage bucket, **When** the file age exceeds 3 days, **Then** the storage layer or cleanup worker automatically purges the file.
2. **Given** violation crop images stored in the private `violations` storage bucket, **When** the raw video is deleted, **Then** the crop images and their database metadata records are preserved permanently.
3. **Given** any client request to view a raw video or violation crop, **When** they request the asset, **Then** the request is mediated via a backend-generated, short-lived signed URL.

### Edge Cases
- **Simultaneous Worker Writes**: Ensure backend worker writes using the service-role key do not trigger RLS locks or block operator reads.
- **Reviewer Profiling**: If an admin profile is deleted or modified, ensure the review logs preserve the operational audit trail (using appropriate delete rules, e.g., setting reviewer reference to null or keeping a static record).
- **Storage Lifecycle Failure**: If the auto-cleanup job fails or is delayed, the system must log an alert to avoid unchecked storage growth.
- **In-Flight Video Processing at Expiration**: If a video is still processing near the 3-day window (rare), it must not be deleted until processing finishes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-012**: The database MUST define a `profiles` table extending `auth.users` that stores user role (`role`, constrained to 'admin' or 'operator') and name (`display_name`).
- **FR-013**: The `videos` table MUST store the operational fields `error_message` (text) and `progress_pct` (integer, constrained between 0 and 100), along with a `processed_at` timestamp.
- **FR-014**: The `videos` table MUST constrain the `model_used` column to one of three supported models ('YOLO', 'RT-DETR', 'Faster R-CNN') via a database check constraint.
- **FR-015**: The `violations` table MUST store the detected violation details, including a `confidence` score (numeric between 0 and 1) and support a nullable `video_id` for live streams.
- **FR-016**: The `violations` table MUST support a manual review workflow using three fields: `reviewed` (boolean, default false), `reviewer_id` (UUID referencing profiles), and `verdict` (constrained to 'confirmed', 'false positive', 'unclear').
- **FR-017**: The database MUST include performance indexes on query-heavy columns:
  - On `videos`: index on `(user_id, status)`
  - On `violations`: index on `(user_id, reviewed, timestamp, model_used)`
- **FR-018**: The system MUST enforce Row Level Security (RLS) policies on `profiles`, `videos`, and `violations` tables:
  - Operators can only read and update records where `user_id` matches their own authentication ID.
  - Administrators bypass RLS restrictions and can read/write all records.
  - Backend services using the Supabase `service_role` key bypass RLS completely.
- **FR-019**: The storage layer MUST create two private buckets: `videos` and `violations`.
- **FR-020**: The storage path conventions MUST follow:
  - For raw videos: `user_id/video_id/filename`
  - For violation crops: `video_id/violation_id/cropname`
- **FR-021**: Client-side access to all storage assets MUST be mediated through temporary signed URLs.
- **FR-022**: The system MUST automatically delete raw video files from the `videos` storage bucket after 3 days, while preserving all violation crops and database records permanently.

### Key Entities *(include if feature involves data)*

- **Profile**: Extension of `auth.users` containing role permissions and operational metadata.
- **Video**: Video file tracker containing status, progress percentage, error messages, and references to model used and processing times.
- **Violation**: Record of a detected non-helmet event, including confidence score, image location, and human review decisions.
- **Storage Bucket (videos)**: Private storage container for raw uploaded footage, with 3-day eviction lifecycles.
- **Storage Bucket (violations)**: Private storage container for cropped high-resolution violation images, kept permanently.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-005**: Filtering and query response times on the `violations` dashboard (by user, status, model, and timestamp) MUST be under 2 seconds when executing queries against a dataset of 10,000 records.
- **SC-006**: Row Level Security policies MUST successfully block 100% of cross-operator query attempts.
- **SC-007**: 100% of raw video files older than 3 days MUST be evicted from storage within 12 hours of their expiration threshold.

## Assumptions

- **Authentication Presence**: The database schema relies on Supabase Auth's `auth.users` table for user management.
- **Worker Environment**: The background workers (Celery/Inference) write to the database using the Supabase `service_role` key, ensuring RLS policies do not restrict their logging or updates.
- **Storage Cleanup implementation**: The 3-day cleanup is assumed to be run either as a scheduled background task or a storage bucket lifecycle policy depending on local deployment limitations.
- **No Direct Storage Exposure**: Client applications will never request direct public URLs for raw videos or violation crops.
