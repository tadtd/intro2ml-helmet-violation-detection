# Tasks: Detection Pipeline Frontend

**Input**: Design documents from `/specs/002-detection-pipeline-frontend/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are optional in this feature and will be written for state and routing validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- Next.js Web App: Files located under `frontend/` directory (e.g., `frontend/app/`, `frontend/store/`, `frontend/components/`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Install dependencies (zustand, @tanstack/react-query, tus-js-client, recharts, papaparse, next-intl, sonner, lucide-react) in [package.json](../../frontend/package.json)
- [x] T002 [P] Configure next-intl localization routing and multi-language JSON files in [messages/vi.json](../../frontend/messages/vi.json) and [messages/en.json](../../frontend/messages/en.json)
- [x] T003 [P] Create TanStack Query client initialization and providers context wrapper in [app/providers.tsx](../../frontend/app/providers.tsx)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core state managers, HTTP client configurations, and route protection middleware

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 [P] Create Zustand stores for user session, file upload queue, and filters in [store/useAuthStore.ts](../../frontend/store/useAuthStore.ts), [store/useUploadStore.ts](../../frontend/store/useUploadStore.ts), and [store/useFilterStore.ts](../../frontend/store/useFilterStore.ts)
- [x] T005 Create global typed API HTTP client with 401 interceptor for silent token refresh in [services/apiClient.ts](../../frontend/services/apiClient.ts)
- [x] T006 Implement role-based and authentication route guard checks in [middleware.ts](../../frontend/middleware.ts)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Detection Loop (Priority: P1) 🎯 MVP

**Goal**: Support video uploads, status tracking, and synced bounding box overlay display.

**Independent Test**: Upload a video, see it added to the queue, transition through processing states, and view player canvas overlay overlays filtering dynamically based on the confidence slider.

- [x] T007 [P] [US1] Build file upload dropzone and queue widget rendering progress and pause/resume buttons in [components/UploadQueue.tsx](../../frontend/components/UploadQueue.tsx)
- [x] T008 [US1] Wire tus-js-client chunked uploading hooks with the Ingestion Service in [app/(app)/upload/page.tsx](../../frontend/app/(app)/upload/page.tsx)
- [x] T009 [US1] Implement bounding box overlays drawn on canvas synced to HTML5 video currentTime via requestAnimationFrame in [components/VideoPlayerWithOverlay.tsx](../../frontend/components/VideoPlayerWithOverlay.tsx)
- [x] T010 [P] [US1] Create violation chronological timeline list that seeks player playback on item click in [components/ViolationTimeline.tsx](../../frontend/components/ViolationTimeline.tsx)
- [x] T011 [P] [US1] Create evidence crop gallery loading static crops from Supabase S3 URLs in [components/EvidenceGallery.tsx](../../frontend/components/EvidenceGallery.tsx)
- [x] T012 [US1] Create operator review flag action updating database records in [components/ViolationReview.tsx](../../frontend/components/ViolationReview.tsx)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - User Authentication & Session Management (Priority: P2)

**Goal**: Login, registration, and user access restrictions.

**Independent Test**: Verify redirection to /login when unauthenticated, and dashboard access permissions according to role.

- [x] T013 [P] [US2] Implement user authentication login and register form forms in [app/login/page.tsx](../../frontend/app/login/page.tsx)
- [x] T014 [US2] Connect login flow to Auth Service, caching token in memory context and active cookie indicator in [app/login/page.tsx](../../frontend/app/login/page.tsx)
- [x] T015 [US2] Create logout button and session clearing actions in [components/Navbar.tsx](../../frontend/components/Navbar.tsx)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Analytics Dashboard & Reporting (Priority: P3)

**Goal**: Display aggregated violations statistics and download CSV/PDF data reports.

**Independent Test**: Navigate to dashboard, check metrics charts adjust based on date filters, download CSV sheet and server-rendered PDF.

- [x] T016 [P] [US3] Integrate Recharts analytics graphs representing time trends, locations, and model metrics comparison in [app/(app)/dashboard/page.tsx](../../frontend/app/(app)/dashboard/page.tsx)
- [x] T017 [US3] Implement CSV file download using PapaParse in [app/(app)/dashboard/page.tsx](../../frontend/app/(app)/dashboard/page.tsx)
- [x] T018 [US3] Implement PDF file download by piping server-rendered document response stream in [app/(app)/dashboard/page.tsx](../../frontend/app/(app)/dashboard/page.tsx)
- [x] T019 [P] [US3] Add admin user management and service health panels in [app/(app)/admin/health/page.tsx](../../frontend/app/(app)/admin/health/page.tsx)

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: User Story 4 - Notifications & Camera Stream View (Priority: P3)

**Goal**: Support WebSocket real-time status alerts and MJPEG/WebRTC live feeds.

**Independent Test**: Trigger a new violation or complete job and verify toast notification, select active camera stream and watch video.

- [x] T020 [P] [US4] Implement WebSocket status update subscriber with polling fallback in [hooks/useWebSocketStatus.ts](../../frontend/hooks/useWebSocketStatus.ts)
- [x] T021 [US4] Configure sonner toast notifications listening to status and violation alerts in [app/layout.tsx](../../frontend/app/layout.tsx)
- [x] T022 [US4] Implement live MJPEG/WebRTC WebSocket stream reader rendering frames on canvas in [app/(app)/camera/page.tsx](../../frontend/app/(app)/camera/page.tsx)

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final builds, security audits, and code optimization.

- [x] T023 [US4] Setup multi-stage Docker build in [Dockerfile](../../frontend/Dockerfile) and dev hot-reloading sync in [Dockerfile.dev](../../frontend/Dockerfile.dev) and [docker-compose.yml](../../docker-compose.yml)
- [x] T024 [US4] Perform final verification runs including ESLint formatting checks in [frontend/](../../frontend/)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
  - User stories can then proceed in parallel or sequentially.
- **Polish (Phase 7)**: Depends on all user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Independent of other stories.
- **User Story 2 (P2)**: Independent of US1 but integrates with components.
- **User Story 3 (P3)**: Independent of US1/US2.
- **User Story 4 (P3)**: Subscribes to backend WS alerts.

---

## Parallel Example: User Story 1

```bash
# Launch models, timelines, and galleries in parallel:
Task: "T007 [P] [US1] Build file upload dropzone and queue widget"
Task: "T010 [P] [US1] Create violation chronological timeline list"
Task: "T011 [P] [US1] Create evidence crop gallery"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories).
3. Complete Phase 3: User Story 1 (Ingestion dropzone, status tracking, video synced canvas).
4. **STOP and VALIDATE**: Verify end-to-end loop from video upload to canvas viewing.

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready.
2. Add User Story 1 -> Test independently -> Deploy/Demo (MVP!).
3. Add User Story 2 -> Test independently -> Deploy/Demo.
4. Add User Story 3 -> Test independently -> Deploy/Demo.
5. Add User Story 4 -> Test independently -> Deploy/Demo.
