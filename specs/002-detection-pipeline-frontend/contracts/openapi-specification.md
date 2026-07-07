# OpenAPI Service Interfaces Mapping

The frontend application interacts with 6 backend microservices through a unified API gateway Ingress, served at `/` and routed by URL prefix pathing.

## 1. Auth Service Contract
* **Base Path**: `/api/v1/auth`

### `POST /login`
* **Description**: Primary authentication login endpoint. Checks credentials, stores refresh token in httpOnly cookie, and returns user metadata and in-memory access token.
* **Payload**:
  ```json
  {
    "username": "operator_or_admin",
    "password": "hashed_or_plain_password"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "userId": "d3b07384-d113-495f-9e7b-e10b2df76a08",
    "fullName": "Nguyen Van A",
    "role": "operator",
    "accessToken": "eyJhbGciOiJIUzI1NiIsIn..."
  }
  ```

### `POST /register`
* **Description**: Register a new user account (primarily for administrative onboarding).
* **Payload**:
  ```json
  {
    "username": "operator_username",
    "password": "password",
    "fullName": "Nguyen Van A",
    "role": "operator"
  }
  ```

### `POST /refresh`
* **Description**: Silent token refresh endpoint. Called via fetch/Axios interceptor when `accessToken` is near expiry. Reads `refreshToken` from the secure httpOnly cookie.
* **Response (200 OK)**:
  ```json
  {
    "accessToken": "eyJhbGciOiJIUzI1NiIsIn..."
  }
  ```
* **Response (401 Unauthorized)**: Redirects client to `/login`.

### `POST /logout`
* **Description**: Clear the current user session and expire the refresh token httpOnly cookie.

---

## 2. Ingestion Service Contract
* **Base Path**: `/api/v1/ingest`

### `POST /upload`
* **Description**: Resumable file upload endpoint conforming to the `tus-js-client` spec.
* **Headers**:
  * `Upload-Length`: size of file in bytes
  * `Upload-Metadata`: metadata tags (filename, user_id, model_used)
  * `Tus-Resumable`: 1.0.0
* **Response (201 Created)**: Returns the resumable upload URL in `Location` header.

---

## 3. Orchestration & Status Service Contract
* **Base Path**: `/api/v1/videos`

### `GET /jobs`
* **Description**: Fetch all detection jobs. Used as fallback polling mechanism if WebSocket is unavailable.
* **Response (200 OK)**:
  ```json
  [
    {
      "jobId": "e12f0f4a-9b48-4061-8409-f6a73c9c6145",
      "fileName": "route_1_morning.mp4",
      "status": "done",
      "modelUsed": "yolo",
      "createdAt": "2026-07-03T04:00:00Z",
      "completedAt": "2026-07-03T04:05:22Z"
    }
  ]
  ```

---

## 4. Dashboard & Query Service Contract
* **Base Path**: `/api/v1/violations`

### `GET /`
* **Description**: Query aggregate violation listings with date ranges and local filters.
* **Query Parameters**:
  * `startDate` (ISO Datetime)
  * `endDate` (ISO Datetime)
  * `model` (yolo | rtdetr | fasterrcnn | all)
  * `status` (pending | approved | dismissed | all)
* **Response (200 OK)**:
  ```json
  [
    {
      "id": "a9bf13de-96b6-4b95-a13a-a1ccb1638202",
      "videoId": "e12f0f4a-9b48-4061-8409-f6a73c9c6145",
      "timestamp": 12.45,
      "bbox": [120, 200, 310, 480],
      "confidence": 0.89,
      "label": "non-helmet",
      "isFlagged": false
    }
  ]
  ```

### `PATCH /{violation_id}`
* **Description**: Operator review action to flag, approve, or dismiss the violation record.
* **Payload**:
  ```json
  {
    "isFlagged": true
  }
  ```

### `GET /pdf`
* **Description**: Triggers a backend dashboard PDF generation. Returns a binary formatted PDF stream.
* **Query Parameters**: Same as `/` (date filters, model filters).

---

## 5. Notification Service Contract
* **Base Path**: `/api/v1/alerts`

### `GET /`
* **Description**: Returns all unread/read system notification feeds.

### `PATCH /{alert_id}`
* **Description**: Mark a notifications alert as read.
