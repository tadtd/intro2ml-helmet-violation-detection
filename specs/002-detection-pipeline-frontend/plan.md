# Implementation Plan: Detection Pipeline Frontend

**Branch**: `002-detection-pipeline-frontend` | **Date**: 2026-07-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from [specs/002-detection-pipeline-frontend/spec.md](file:///e:/hcmus/semester-6/intro2ml-helmet-violation-detection/specs/002-detection-pipeline-frontend/spec.md)

## Summary
Implement a high-performance, localized traffic operations web frontend using Next.js (App Router), TypeScript, and Tailwind CSS. The app features state separation: TanStack Query manages async server state (dashboard aggregation, job list, violations list) while Zustand manages synchronous client state (multi-file upload progress tracking, timeline search filters, and auth profiles). The UI is built using shadcn/ui components. File upload uses `tus-js-client` for chunked, resumable ingestion. The video results page features a custom bounding box canvas layer synchronized to video playback via `requestAnimationFrame`. Telemetry charts are visualized with Recharts, exports use `papaparse` for CSV and API-based PDF generation, and notifications use `sonner` driven by WebSockets. The system defaults to Vietnamese (`vi`) with a toggle for English (`en`).

## Technical Context

**Language/Version**: TypeScript 5.x, Node.js v18

**Primary Dependencies**: Next.js 16.x (App Router), React 19.x, Zustand v4, @tanstack/react-query v5, Tailwind CSS v4, shadcn/ui, tus-js-client, video.js, Recharts, papaparse, next-intl, sonner, openapi-typescript (OpenAPI client generator)

**Storage**: LocalStorage (user preference cache), Cookies (refresh token), Memory (access token)

**Testing**: Jest + React Testing Library (components, hooks, routing), Playwright (E2E upload/monitoring flows)

**Target Platform**: GKE Standard (Docker container behind Traefik API Ingress, served at `/`)

**Project Type**: Next.js Web Application

**Performance Goals**:
* Bounding box overlays render in sync with video frames (drift <50ms) using `requestAnimationFrame`.
* Confidence slider filters results locally in under 100ms.
* Interface transitions and toast alerts respond within 150ms.

**Constraints**:
* Strict cross-service typed OpenAPI client synchronization.
* Auth access token must be kept in memory, not in localStorage.
* No client-side PDF generation (call backend endpoint to keep styling consistent).

**Scale/Scope**:
* Single Next.js standalone container deployment.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Constraint | Status | Notes |
|------------------------|--------|-------|
| I. Code Quality & Interface Standardization | ✅ PASS | Frontend uses TypeScript with typed OpenAPI generation (`openapi-typescript`). Strictly uses npm. |
| II. Comprehensive Testing Discipline | ✅ PASS | Component unit tests and E2E WebSockets/upload tests will run in CI. |
| III. Responsive UI/UX and Live Feedback Loop | ✅ PASS | Bounding boxes sync using canvas and `requestAnimationFrame`. Real-time status list updates via WebSockets. |
| IV. Performance Optimization & Resource Efficiency | ✅ PASS | Slider filters overlays client-side (no re-fetches). Large file uploads use chunked TUS protocol to avoid timeouts. |
| V. Rigorous Data Governance & Observability | ✅ PASS | i18n via `next-intl` (Vietnamese default). Secure in-memory token storage + httpOnly cookie session management. |
| Core Stack & Local Orchestration | ✅ PASS | Frontend uses Next.js, Dockerized and orchstrated locally via Docker Compose. |

## Project Structure

### Documentation (this feature)

```text
specs/002-detection-pipeline-frontend/
├── plan.md              # This file
├── research.md          # State management architectures, video overlays sync, and i18n
├── data-model.md        # Client-side Zustand stores schemas and Types
├── quickstart.md        # Setup local development environment and client code generation
└── contracts/           # OpenAPI client spec schema mapping
```

### Source Code (repository root layout)

```text
frontend/
├── app/                 # Next.js App Router (layout, dashboard, upload, camera, login)
├── components/          # Reusable UI elements (shadcn/ui custom wrappers)
├── hooks/               # Custom React hooks (WS notifications, video overlays)
├── services/            # OpenAPI generated HTTP client and interceptors
├── store/               # Zustand state stores (upload, filters, session)
├── messages/            # next-intl translation dictionaries (vi.json, en.json)
├── public/              # Static assets (images, fonts, mock videos)
├── middleware.ts        # Next.js middleware for auth guards and localization routing
├── next.config.ts       # Standalone build settings
├── package.json         # Dependency configuration
├── Dockerfile           # Standalone Node.js alpine build configuration
└── Dockerfile.dev       # Development hot-reloading build configuration
```

**Structure Decision**: Standard Next.js App Router directory layout placed under the `frontend/` repository root directory.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| In-Memory JWT Storage | Enhanced security; prevents XSS attacks from stealing credentials. | Storing JWT in LocalStorage is simpler, but exposes sensitive traffic officer credentials to scripts. |
| OpenAPI Codegen Client | Maintains tight client-server typed contracts across all backend microservices. | Writing manual Fetch wrappers is simpler, but highly prone to drift errors during API upgrades. |
| Server-Side PDF Export | Guarantees consistent formatting, page breaks, and styling regardless of local browser. | Client-side Canvas/PDF tools are simpler, but produce low-quality results and inconsistent layouts. |
