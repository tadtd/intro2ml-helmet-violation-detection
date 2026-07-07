# Camera & WebSocket Module — Implementation Flow

## 1. Architecture Overview

```
┌─────────────────┐   JPEG frames (binary, 10 FPS)   ┌──────────────────────┐
│  Frontend        │ ───────────────────────────────▶ │  WS Endpoint          │
│  camera/page.tsx │                                    │  routes/camera.py     │
│                  │ ◀─────────────────────────────── │                        │
└─────────────────┘   JSON {detections, violations}    │  ┌──────────────────┐ │
                                                         │  │ run_inference()  │ │
                                                         │  └────────┬─────────┘ │
                                                         │           ▼           │
                                                         │  ┌──────────────────┐ │
                                                         │  │ IoUTracker        │ │
                                                         │  └────────┬─────────┘ │
                                                         │           ▼           │
                                                         │  ┌──────────────────┐ │
                                                         │  │ find_violations() │ │
                                                         │  └────────┬─────────┘ │
                                                         │           ▼           │
                                                         │  async save (S3+DB)   │
                                                         └──────────────────────┘
```

One `IoUTracker` instance lives **per WebSocket connection** (per camera session) — trackers must not be shared across clients.

---

## 2. WebSocket Protocol

**Connection lifecycle:**

| Step | Direction | Payload | Type |
|---|---|---|---|
| 1 | Client → Server | JWT token | `text` |
| 2 | Server → Client | `{"status": "authenticated"}` or close(4401) | `text` |
| 3 | Client → Server | JPEG frame | `bytes` |
| 4 | Server → Client | detection/violation result | `text` (JSON) |
| 3–4 repeat until disconnect | | | |

**Server → Client JSON schema per frame:**
```json
{
  "frame_id": 1029,
  "boxes": [
    {"track_id": 7, "class": "motorbike", "bbox": [x1,y1,x2,y2], "conf": 0.91},
    {"track_id": 12, "class": "no-helmet", "bbox": [x1,y1,x2,y2], "conf": 0.88, "violation": true}
  ],
  "violation_count": 3
}
```

Rules:
- `track_id` is always present (from `IoUTracker`), even for the mock — required for correct frontend counting.
- `violation": true` is only set on boxes matched by `find_violations()`.
- `violation_count` = number of **distinct track_ids** flagged so far this session, not frames.

---

## 3. Backend Flow (`routes/camera.py`)

```python
@router.websocket("/ws/camera")
async def camera_ws(websocket: WebSocket):
    await websocket.accept()

    # --- Step 1: Auth gate ---
    token = await websocket.receive_text()
    user = verify_jwt(token)                 # raises -> close(4401)
    if not user:
        await websocket.close(code=4401)
        return
    await websocket.send_json({"status": "authenticated"})

    tracker = IoUTracker()                   # one per connection
    seen_violation_ids: set[int] = set()      # for violation_count + dedup window
    frame_id = 0

    try:
        while True:
            frame_bytes = await websocket.receive_bytes()
            frame_id += 1

            detections = run_inference(frame_bytes)          # stub -> real model later
            tracked = tracker.update(detections)              # assigns track_id
            violations = find_violations(tracked)             # pairs no-helmet <-> motorbike

            for v in violations:
                if v.track_id not in seen_violation_ids:
                    seen_violation_ids.add(v.track_id)
                    asyncio.create_task(save_violation(user, frame_bytes, v))  # fire-and-forget

            await websocket.send_json(build_payload(frame_id, tracked, violations, seen_violation_ids))

    except WebSocketDisconnect:
        tracker.reset()
    except Exception as e:
        logger.exception("camera_ws error")
        await websocket.close(code=1011)
```

`save_violation` must never block the frame loop — always dispatched via `asyncio.create_task` (or a queue/worker if volume is high).

---

## 4. `app/tracker.py` — `IoUTracker`

**Responsibility:** turn per-frame detections into persistent tracks across frames.

```python
class Track:
    id: int
    bbox: tuple[float, float, float, float]
    cls: str
    lost_frames: int = 0

class IoUTracker:
    def __init__(self, iou_threshold=0.3, max_lost=10):
        self.tracks: dict[int, Track] = {}
        self.next_id = 1
        self.iou_threshold = iou_threshold
        self.max_lost = max_lost

    def update(self, detections: list[Detection]) -> list[Track]:
        """
        1. Compute IoU matrix between existing tracks and new detections.
        2. Greedily match pairs above iou_threshold (highest IoU first)
           — or use scipy.optimize.linear_sum_assignment for optimal matching.
        3. Matched: update track.bbox, reset lost_frames = 0.
        4. Unmatched detections: create new Track(id=next_id), next_id += 1.
        5. Unmatched tracks: lost_frames += 1; drop if lost_frames > max_lost.
        6. Return list of currently active tracks (with class + bbox + id).
        """

    def reset(self):
        self.tracks.clear()
```

**IoU helper:**
```python
def iou(box_a, box_b) -> float:
    # standard intersection-over-union on [x1,y1,x2,y2]
```

Key design point: matching is **greedy-by-IoU-descending** for simplicity in v1; swap to Hungarian algorithm (`scipy.optimize.linear_sum_assignment`) if track-swapping becomes an issue with dense scenes.

---

## 5. `app/violation_logic.py`

### `find_violations(tracks)`

**Responsibility:** pair `no-helmet` boxes with the nearest `motorbike` box.

```python
def find_violations(tracks: list[Track]) -> list[Violation]:
    motorbikes = [t for t in tracks if t.cls == "motorbike"]
    no_helmets = [t for t in tracks if t.cls == "no-helmet"]

    violations = []
    for person in no_helmets:
        nearest = min(
            motorbikes,
            key=lambda m: centroid_distance(person.bbox, m.bbox),
            default=None
        )
        if nearest and centroid_distance(person.bbox, nearest.bbox) < DISTANCE_THRESHOLD:
            violations.append(Violation(track_id=person.id, bbox=person.bbox, motorbike_id=nearest.id))
    return violations
```

- Association metric: centroid distance (simpler, robust to partial overlap) with IoU as a fallback tie-breaker if two motorbikes are equidistant.
- `DISTANCE_THRESHOLD` should scale with frame resolution — tune empirically.

### Deduplication (one crop per `track_id` per violation window)

Handled at the **caller level** (`camera.py`), not inside `find_violations` — keeps the function pure/stateless and testable. Session-scoped `seen_violation_ids: set[int]` acts as the dedup gate; only the *first* frame a given `track_id` is flagged triggers a save.

For longer sessions, replace the plain `set` with a **windowed dedup** so the same physical rider re-entering later is treated as a new violation:
```python
class ViolationWindow:
    def __init__(self, window_seconds=30):
        self.last_saved: dict[int, float] = {}   # track_id -> timestamp
        self.window = window_seconds

    def should_save(self, track_id: int) -> bool:
        now = time.time()
        last = self.last_saved.get(track_id)
        if last is None or (now - last) > self.window:
            self.last_saved[track_id] = now
            return True
        return False
```

---

## 6. Frontend Flow (`app/(app)/camera/page.tsx`)

**State:** `videoRef`, `canvasRef`, `wsRef`, `violationIds: Set<number>`, `connected: boolean`.

```
1. onMount:
   - getUserMedia({video: true}) -> attach stream to <video>
   - do NOT auto-connect WS; wait for user "Connect" click

2. onConnect():
   - open WebSocket
   - onopen: send(jwtToken)               // text frame, step 1 of protocol
   - onmessage (first): expect {"status":"authenticated"} -> setConnected(true)
   - if server closes with 4401: show "session expired" -> redirect to login

3. Frame loop (starts only after authenticated):
   - prefer request/response pacing over blind setInterval:
       async function loop() {
         while (connected) {
           drawVideoFrameToOffscreenCanvas();
           const blob = await canvasToBlob("image/jpeg", 0.7);
           ws.send(blob);
           await waitForNextMessageOrTimeout(150ms);  // paced by server response
         }
       }
   - fallback: setInterval(100ms) if pacing proves unnecessary in practice

4. onmessage (subsequent):
   - parse JSON -> {boxes, violation_count}
   - clear visible canvas
   - for each box: draw rect, green if !violation, red if violation
   - scale bbox coords: displayed_coord = raw_coord * (canvas.clientWidth / video.videoWidth)
   - update violationIds with any new track_ids flagged -> setViolationCount(violationIds.size)

5. onDisconnect() / unmount:
   - clearInterval / stop loop
   - stream.getTracks().forEach(t => t.stop())
   - ws.close()
```

**Core component sketch:**
```tsx
function CameraPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const violationIds = useRef<Set<number>>(new Set());
  const [violationCount, setViolationCount] = useState(0);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(stream => { videoRef.current!.srcObject = stream; })
      .catch(() => setError("Camera permission denied"));
    return () => stopAllTracks();
  }, []);

  function connect() { /* step 2 above */ }
  function disconnect() { /* step 5 above */ }

  return (/* video + canvas overlay + connect button + violation counter */);
}
```

---

## 7. Error Handling Checklist

| Failure | Handling |
|---|---|
| `getUserMedia` denied | Show inline error, don't attempt WS connect |
| JWT invalid/expired | Server closes with code `4401`; frontend shows re-auth prompt |
| WS drops mid-session | `onclose` → stop frame loop, show "reconnect" button; tracker resets server-side |
| Frame decode failure (corrupt JPEG) | Backend catches per-frame, sends `{"error": "decode_failed"}`, continues loop (no crash) |
| Backend save failure (S3/DB) | Logged, does not affect live stream (fire-and-forget task) |

---

## 8. Suggested Build Order

1. `IoUTracker` + unit tests (synthetic box sequences)
2. `find_violations` + dedup window, unit tests
3. `camera.py` with JWT gate, stub `run_inference`, wired to tracker + violation logic
4. Frontend webcam capture + WS auth handshake
5. Frontend draw loop with coordinate scaling and live counter
6. Swap `run_inference` stub for real model — no protocol changes needed
