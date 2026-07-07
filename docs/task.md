### Member 4 — WebSocket & Camera Page

**Backend WebSocket (`routes/camera.py`)**

- Accept WebSocket connection, verify JWT from first message
- Receive JPEG-encoded frames from client
- Call `run_inference()` per frame (stub first, real later)
- Call `find_violations()` from `violation_logic.py`
- Send back detection boxes and violation flags as JSON
- Save realtime violations asynchronously (upload crop, insert row)

**`app/tracker.py`**

- Implement `IoUTracker`: match detections across frames by IoU, assign persistent `track_id`, handle lost tracks

**`app/violation_logic.py`**

- Implement `find_violations()`: associate `non-helmet` boxes with nearest motorbike box by centroid distance or IoU
- Implement deduplication: one crop saved per `track_id` per violation window to avoid repeated saves

**Frontend Camera Page (`app/(app)/camera/page.tsx`)**

- Access webcam via `getUserMedia`
- Capture frames at ~10 FPS and send as JPEG bytes over WebSocket
- Parse incoming JSON (detections + violations)
- Draw bounding boxes on a canvas overlay (green = ok, red = violation)
- Show live violation count