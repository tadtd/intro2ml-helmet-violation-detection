# Feature Specification: Helmet Violation Detection System

**Feature Branch**: `001-detect-helmet-violations`

**Created**: 2026-07-02

**Status**: Ready

**Input**: User description: "build an web system for detecting motorcycle helmet violations. i want this application to be complete, production-ready solution that can genuinely assist traffic police officers in their daily work"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Video Upload & Automated Violation Detection (Priority: P1)
As a traffic police officer (operator), I want to upload a traffic video and select a detection model (YOLO, RT-DETR, or Faster R-CNN) so that the system automatically detects, tracks, and extracts motorcycle helmet violations asynchronously using rule-based heuristics.

**Why this priority**: Core value proposition. Uploading recorded video feeds for automated analysis enables officers to process hours of traffic video footage without manual review.

**Independent Test**: Can be fully tested by uploading a test video, selecting a model, waiting for processing to complete, and verifying that detected riders without helmets are logged with coordinates, timestamps, and combined context image crops.

**Acceptance Scenarios**:
1. **Given** an authenticated operator on the video upload dashboard, **When** they upload a video file and select "YOLO", **Then** the video status is set to `pending`, and a background processing job is queued.
2. **Given** a background processing job starts, **When** the processing finishes successfully, **Then** the video status updates to `done`, and the processed video is annotated with bounding boxes around motorbikes, helmets, and non-helmets.
3. **Given** a processing job is completed, **When** the operator views the results page, **Then** they see a chronological list of violations detected, each displaying the corresponding track ID, timestamp, and a direct link to the cropped violation image showing the rider and vehicle context.
4. **Given** a video processing job fails (e.g., due to file corruption), **When** the system encounters the error, **Then** the video status transitions to `failed`, and a user-friendly error description is displayed.

---

### User Story 2 - Realtime Live Camera Monitoring & Alerting (Priority: P2)
As a traffic officer on duty, I want to connect to a live camera stream and receive real-time, low-latency visual overlays and instant alert feeds of helmet violations so that I can take immediate enforcement action.

**Why this priority**: Realtime monitoring is crucial for active roadside checkpoints where officers need immediate notifications to flag down violators.

**Independent Test**: Can be fully tested by initiating a simulated video stream, connecting via WebSocket, and verifying that frames are rendered with bounding boxes and violation alerts are appended to the feed with minimal latency.

**Acceptance Scenarios**:
1. **Given** an authenticated officer on the Camera stream page, **When** they select a camera feed and click "Start Monitoring", **Then** a secure WebSocket connection is established, and the live video stream displays with less than 100ms frame latency.
2. **Given** a live stream is actively running, **When** a rider without a helmet passes the camera field of view, **Then** a red bounding box is overlayed around the rider in real-time, and a snapshot of the violation is saved to the evidence database.
3. **Given** a new violation is detected on the live feed, **When** it is saved to the database, **Then** the live alert feed is immediately updated via in-app visual and audio alerts, combined with browser-based native desktop notifications.

---

### User Story 3 - Violation Evidence Management & Auditing (Priority: P3)
As a traffic department administrator, I want to review all logged violations, inspect high-quality image crops as evidence, filter logs, and manage the lifecycle of recorded violations.

**Why this priority**: Necessary for legal validity. Traffic officers must inspect high-quality, uncompressed evidence (rider crops) before officially issuing citations or fines.

**Independent Test**: Can be fully tested by logging in as an administrator, navigating to the Violation Log, applying various filters (date range, model, user), and verifying that only authorized data is visible and exports function correctly.

**Acceptance Scenarios**:
1. **Given** an authenticated administrator, **When** they access the Violation Log, **Then** they can view violations logged by all operators, whereas a standard operator can only view their own violations (enforced via Row Level Security).
2. **Given** a violation record, **When** the administrator clicks on it, **Then** they view a high-resolution crop showing the composite union box of the violating rider and their motorbike, the motorbike track ID, and the exact timestamp of detection.
3. **Given** a collection of violations, **When** the administrator filters by date and detection model, **Then** the list instantly updates to show only matching violations.
4. **Given** the list of logged violations and original video files, **When** the storage limit is approached, **Then** the files are managed according to retaining violation evidence crops and database records permanently while auto-deleting raw uploaded video files after 3 days to manage storage limits.
5. **Given** a violation is inspected by an officer, **When** they decide to process it, **Then** it follows the workflow of a manual review status toggle (Approved vs. Dismissed) managed directly by the traffic officer.

### Edge Cases
- **Duplicate Tracking IDs**: If a motorbike tracker loses a track and re-acquires it as a new track ID, the system must not create duplicate violation records for the same physical vehicle within a narrow time window.
- **WebSocket Disconnection**: If the network connection drops during a live stream, the client must display a clear reconnection overlay and attempt to automatically re-establish the socket connection.
- **Low Light/Weather Conditions**: Under poor visibility, if detection confidence falls below the default threshold (50%), the system must log a debug status to avoid false-positive alerts while still recording telemetry.
- **Stationary Motorbikes**: To prevent pedestrians walking near parked motorbikes from triggering false violations, the system must apply a velocity-based motion heuristic. Violations are only generated for motorbikes that demonstrate clear movement (displacement over a window of frames).

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: The system MUST allow traffic officers and administrators to log in using Supabase Auth.
- **FR-002**: The system MUST allow operators to upload videos in standard formats (MP4, AVI) to Supabase Storage.
- **FR-003**: The backend MUST process videos asynchronously using Celery task workers to avoid blocking HTTP request threads.
- **FR-004**: The system MUST support running inference with three model options: YOLO, RT-DETR, and Faster R-CNN, configured via ONNX Runtime.
- **FR-005**: The system MUST perform frame-by-frame object detection, mapping classes to motorbikes, helmets, and riders without helmets (non-helmet).
- **FR-006**: The system MUST track motorbikes across frames and assign unique track IDs using a tracking algorithm.
- **FR-007**: The system MUST calculate and crop the composite union bounding box of the violating rider (`non-helmet` box) and the associated `motorbike` box as the evidence image, ensuring the crop contains both the face of the rider and the vehicle context (for manual license plate identification).
- **FR-008**: The system MUST apply tracking velocity/displacement heuristics to filter out false-positive violations from stationary/parked motorbikes.
- **FR-009**: The system MUST support WebSocket-based live camera stream monitoring, overlaying detections with latency below 100ms.
- **FR-010**: The database queries for videos and violations MUST enforce Row Level Security (RLS) policies to restrict operator visibility.
- **FR-011**: The web application interface MUST support localization (i18n), with Vietnamese (`vi`) as the default language and English (`en`) as the secondary option.

### Key Entities
- **User Profile**: Represents a traffic officer or administrator. Includes ID (UUID from Supabase Auth), full name, role (operator or admin), and creation timestamp.
- **Video**: Represents a video uploaded for processing. Includes ID, user_id, filename, storage_path, model_used, status (pending, processing, done, failed), and created_at.
- **Violation**: Represents a single detected non-helmet incident. Includes ID, video_id (null if live camera), user_id, track_id, model_used, image_url (composite evidence crop containing motorbike + violating head), and timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes
- **SC-001**: Operators can upload a 100MB video and see it start processing in under 5 seconds.
- **SC-002**: The system processes uploaded videos at a rate of at least 15 frames per second during background inference.
- **SC-003**: 95% of live camera stream frames are processed and rendered with bounding boxes in under 100ms round-trip latency.
- **SC-004**: 100% of detected helmet violations correctly log a unique track ID and upload a composite evidence crop containing the vehicle.
- **SC-005**: Administrators can query and filter through 10,000 violation records in under 2 seconds.

## Assumptions
- **User Internet Connectivity**: Officers have stable broadband connection at traffic offices and 4G/5G connection at roadside checkpoints.
- **ALPR Boundary**: Automated license plate recognition is out of scope for v1. Officers manually review the composite video/image crop to read the plate number if needed.
- **Camera Inputs**: Live streams are ingested as MJPEG/RTSP stream frames converted backend-side and pushed to WebSockets.
- **Weights Availability**: Pre-trained model weights for YOLO, RT-DETR, and Faster R-CNN are provided in ONNX format.
- **Localization**: The application user interface defaults to Vietnamese (`vi`) for all system texts, labels, and violation statuses, with a global toggle option to switch to English (`en`).

## Clarifications

### Session 2026-07-03
- Q: Where should the backend microservices be located in the repository? → A: Moved inside the backend/ directory.


