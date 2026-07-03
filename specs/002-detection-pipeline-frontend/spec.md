# Feature Specification: Detection Pipeline Frontend

**Feature Branch**: `002-detection-pipeline-frontend`

**Created**: 2026-07-03

**Status**: Ready

**Input**: User description: "Right now, there is spec about backend so this spec focused on FE (UI/UX). The frontend covers the full user journey around the detection pipeline: authentication, upload, status tracking, results representation, and dashboard."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Detection Loop: Upload, Status Tracking, and Results (Priority: P1)

As a traffic operator, I want to upload traffic videos, track their processing status, and view the annotated violation results in an interactive video player so that I can quickly identify and audit helmet violations.

**Why this priority**: This represents the core MVP loop. A user must be able to complete the entire pipeline from file ingestion to viewing results and understanding aggregate stats.

**Independent Test**: Can be fully tested by uploading a test video, watching the progress bar and queue status, seeing the status transition from pending to processing to done, viewing the annotated results, seeking through the video player using the violation timeline, and adjusting the confidence threshold slider.

**Acceptance Scenarios**:

1. **Given** an operator on the video upload screen, **When** they drag-and-drop a video file and click upload, **Then** client-side validation verifies the format and file size, and the file is added to a multi-file upload queue with a real-time progress bar.
2. **Given** a queued file upload, **When** the upload completes, **Then** the video record is created in the database and transitions to the job status list showing the job status as `pending`.
3. **Given** a detection job in the status list, **When** the backend starts processing it, **Then** the status dynamically updates to `processing` without requiring a manual page refresh.
4. **Given** a detection job finishes successfully, **When** the operator clicks "View Results", **Then** they are taken to the Results page containing:
   - A video player with bounding box overlays showing detected motorbikes, helmets, and non-helmet riders.
   - A chronological list of violations with timestamps. Clicking a violation seeks the video player directly to that timestamp.
   - A snapshot gallery showing evidence crops of detected violations.
   - A confidence threshold slider that filters the overlays, timeline, and gallery in real-time.
   - A review action to flag/approve/dismiss the violation record.

---

### User Story 2 - User Authentication & Session Management (Priority: P2)

As a system user, I want to register, log in, and maintain a secure session with appropriate user access levels so that my data is protected and admin controls are restricted to authorized personnel.

**Why this priority**: Role-based access control and security are critical for government and operator workflows, but can be simulated or bypassed during initial prototyping.

**Independent Test**: Can be fully tested by attempting to access protected dashboard routes as an unauthenticated user (verifying redirection to login), logging in as an Operator (verifying admin panels are hidden), logging in as an Admin (verifying user management and health dashboards are visible), and logging out to verify session clearance.

**Acceptance Scenarios**:

1. **Given** an unauthenticated visitor, **When** they navigate to any protected route (e.g., dashboard, upload, results), **Then** they are redirected to the Login page.
2. **Given** a user logging in, **When** the Auth Service validates their JWT, **Then** the application stores the token, initiates session refresh in the background, and redirects them based on their user role (`operator` or `admin`).
3. **Given** an authenticated user with the `operator` role, **When** they access the navigation menu, **Then** they only see options for upload, tracking, and basic dashboards, and cannot access the admin user management.
4. **Given** an authenticated user with the `admin` role, **When** they log in, **Then** they have full access to user management lists and service health status indicators.

---

### User Story 3 - Analytics Dashboard & Reporting (Priority: P3)

As a traffic department manager, I want to view aggregated violation data, trends, and comparisons, and export reports in PDF and CSV formats so that I can report traffic safety metrics.

**Why this priority**: Post-processing analytics and exports are essential for auditing and reporting, but are secondary to the core detection engine.

**Independent Test**: Can be fully tested by navigating to the Dashboard, applying date and location filters, observing the charts update, and clicking export buttons to download CSV/PDF reports.

**Acceptance Scenarios**:

1. **Given** an operator on the Dashboard, **When** they select a date range and location filter, **Then** the violation count, trends, and camera breakdown charts update dynamically.
2. **Given** an operator viewing the dashboard, **When** they click "Export to CSV", **Then** the browser downloads a spreadsheet containing the filtered list of violations, timestamps, and metadata.
3. **Given** an operator viewing the dashboard, **When** they click "Export to PDF", **Then** the browser downloads a formatted report summary containing trend charts and summary metrics.

---

### User Story 4 - Notifications & Camera Stream View (Priority: P3)

As an operator, I want to receive real-time notifications for newly completed jobs and select camera streams to monitor so that I remain aware of system activities.

**Why this priority**: Notifications and camera source views are supporting operations that increase usability and long-term utility but are not required for MVP testing.

**Acceptance Scenarios**:

1. **Given** an active operator session, **When** a background detection job completes or a new violation is detected on a live feed, **Then** an in-app toast notification appears prompting the operator to view the result, and updates the in-app alert feed status.
2. **Given** an operator, **When** they navigate to the Camera Monitoring tab, **Then** they can select from a predefined list of active camera streams to monitor live WebSocket video feeds.

### Edge Cases

- **Large File Interruption**: If the network connection drops during a large video upload, the client must pause the upload and resume from the last successful chunk when the connection is restored.
- **Inference Failure Handling**: If a background detection job fails, the status tracker must display a user-friendly error message detailing the reason (e.g., video corrupt, unsupported codec) and offer a re-try action.
- **Concurrent Dashboard Updates**: If multiple violations are detected concurrently, the dashboard trend charts and realtime violation feeds must throttle updates to avoid UI stutter/freezes.
- **Expired Sessions**: If the JWT session expires and token refresh fails while the user is actively analyzing results, the application must save the current state locally and prompt the user to re-authenticate via a modal without reloading the page.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: **Authentication & JWT**: Users MUST be able to log in, register, and log out. The frontend MUST securely store JWT tokens and handle token refresh with the Auth Service.
- **FR-002**: **Role-Based Routing**: The application MUST enforce client-side route guard routing and view-filtering based on roles (`admin` vs. `operator`).
- **FR-003**: **File Dropzone Ingestion**: The system MUST support drag-and-drop video/image uploads.
- **FR-004**: **Client-Side Validation**: The frontend MUST validate files (file extension, size limitations) prior to initiating uploads.
- **FR-005**: **Chunked Upload & Progress Bar**: The frontend MUST upload files using a chunked protocol and render a real-time progress percentage bar.
- **FR-006**: **Upload Queue Manager**: The system MUST support tracking multiple concurrent uploads in an upload queue.
- **FR-007**: **Real-Time Job Tracker**: The system MUST track job states (`pending` -> `processing` -> `done`/`failed`) in real-time or via short polling, matching the backend DB status values.
- **FR-008**: **Annotated Video Player**: The system MUST display a video player overlaid with bounding box bounding boxes around violating riders and motorbikes.
- **FR-009**: **Timestamp Timeline**: The results page MUST show a list of violations with exact timestamps. Clicking an item MUST seek the video player to the correct timestamp.
- **FR-010**: **Evidence Crop Gallery**: The results page MUST display a gallery of static high-resolution crops showing violation evidence from the `violations` storage bucket.
- **FR-011**: **Confidence Threshold Filter**: The interface MUST provide a slider to filter overlays and list elements dynamically based on model confidence.
- **FR-012**: **Manual Flag & Review**: Operators MUST be able to flag false-positive detections, updating their status.
- **FR-013**: **Analytics Charts**: The dashboard MUST show total violations grouped by time range, camera/location, and model type.
- **FR-014**: **Model Benchmarking Dashboard**: System MUST support comparing model metrics (`yolo`, `rtdetr`, `fasterrcnn`) dynamically using database logs matching the model identifiers in the backend.
- **FR-015**: **CSV/PDF Export**: The dashboard MUST support exporting filtered lists and charts to CSV and PDF formats.
- **FR-016**: **Toast Notifications**: The system MUST display in-app toast alerts when a new violation is detected or when a background job status updates.
- **FR-017**: **Live Camera View Selection**: Operators MUST be able to select and watch live camera feeds from a preconfigured set of WebSocket endpoints (e.g. `/ws/camera`). Modifying or adding new cameras dynamically is out of scope for the MVP.
- **FR-018**: **System Health dashboard**: Admins MUST have a dedicated view to inspect service health statuses.

### Key Entities

- **UserSession**:
  - `userId`: UUID
  - `role`: "admin" | "operator"
  - `accessToken`: JWT String
  - `refreshToken`: JWT String
- **UploadQueueItem**:
  - `id`: String
  - `fileName`: String
  - `progress`: Number (0-100)
  - `status`: "uploading" | "paused" | "completed" | "failed"
- **DetectionJob**:
  - `jobId`: UUID
  - `status`: "pending" | "processing" | "done" | "failed"
  - `fileName`: String
  - `modelUsed`: "yolo" | "rtdetr" | "fasterrcnn"
  - `createdAt`: Timestamp
  - `completedAt`: Timestamp
- **ViolationOverlay**:
  - `timestamp`: Number (seconds)
  - `bbox`: Array of Numbers `[x1, y1, x2, y2]`
  - `confidence`: Number (0.0-1.0)
  - `label`: "non-helmet" | "helmet" | "motorbike"
  - `isFlagged`: Boolean
- **Alert**:
  - `id`: UUID
  - `violationId`: UUID
  - `userId`: UUID
  - `status`: "unread" | "read"
  - `createdAt`: Timestamp

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Large file uploads (up to 500MB) can be paused/resumed and report progress within a +/- 1% accuracy range.
- **SC-002**: Bounding boxes render on the video player in sync with the video timeline within a maximum drift of 50ms.
- **SC-003**: The results filtering panel updates the list of violations and overlays in under 100ms when the confidence threshold slider is adjusted.
- **SC-004**: Users can complete a review action (approving/flagging a violation) in under 2 clicks.
- **SC-005**: All UI actions respond with appropriate visual states within 150ms of user interaction.

## Assumptions

- **Target Device Screen Size**: The dashboard and results player are optimized for desktop/tablet screens (minimum width 1024px); mobile optimization is out of scope for the MVP.
- **Backend API Availability**: The frontend assumes the Ingestion, Detection, and Auth microservices conform to the REST and WebSocket contracts.
- **Language Localization**: The application defaults to Vietnamese (`vi`) with a translation toggle to switch to English (`en`).
- **File Upload Limits**: A single file size limit of 1GB is enforced client-side.

## Clarifications

### Session 2026-07-03

- Q: What are the exact user roles in the system? → A: Aligned with the backend schema: `operator` and `admin`.
- Q: What are the exact states for detection jobs? → A: Aligned with the backend schema: `pending`, `processing`, `done`, and `failed`.
- Q: How is camera source management handled in the MVP? → A: Pre-configured camera selection list. Modifying or adding camera sources dynamically is out of scope.
- Q: Is model benchmarking comparison included? → A: Yes, compared across backend model keys (`yolo`, `rtdetr`, `fasterrcnn`).
