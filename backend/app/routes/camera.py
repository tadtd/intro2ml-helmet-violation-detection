import asyncio
import random
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..tracker import IoUTracker
from ..violation_logic import find_violations, ViolationWindow
from ..models.base import Detection

router = APIRouter(tags=["camera"])

# Async mock saving task
async def save_violation(user: str, frame_bytes: bytes, violation: object):
    # Simulated upload/database insert delay (fire-and-forget task)
    await asyncio.sleep(0.2)
    # print(f"Saved violation for user {user}, track_id: {violation.track_id}")

@router.websocket("/ws/camera")
async def camera_socket(websocket: WebSocket) -> None:
    await websocket.accept()

    # --- Step 1: Auth gate ---
    try:
        # We expect the client to send a JWT as a text payload first.
        # For now, we mock JWT verification.
        token = await websocket.receive_text()
        
        # MOCK JWT CHECK (Replace with real verify_jwt(token))
        user = "mock_user_123"
        if not user:
            await websocket.close(code=4401)
            return
            
        await websocket.send_json({"status": "authenticated"})
    except WebSocketDisconnect:
        return
        
    tracker = IoUTracker()
    violation_window = ViolationWindow(window_seconds=30.0)
    seen_violation_ids: set[int] = set() # For counting total unique violations in session
    frame_id = 0
    
    try:
        while True:
            # --- Step 2: Binary Frame Parsing & Processing ---
            frame_bytes = await websocket.receive_bytes()
            frame_id += 1
            
            # --- MOCK ML INFERENCE ---
            # Generate random mock detections instead of calling run_inference(frame_bytes)
            mock_detections = []
            
            # 50% chance to generate a random motorbike
            if random.random() > 0.5:
                x = random.randint(50, 400)
                y = random.randint(50, 300)
                mock_detections.append(Detection(
                    class_name="motorbike",
                    box=(x, y, x + 150, y + 150),
                    confidence=0.9
                ))
                
            # 30% chance to generate a no-helmet rider near the motorbike
            if mock_detections and random.random() > 0.7:
                mx = mock_detections[0].box[0]
                my = mock_detections[0].box[1]
                mock_detections.append(Detection(
                    class_name="non-helmet",
                    box=(mx + 20, my - 40, mx + 80, my + 20),
                    confidence=0.85
                ))
            
            # --- ML TRACKING & VIOLATION MATCHING ---
            # 1. Tracker assigns persistent track_ids
            tracked = tracker.update(mock_detections)
            
            # 2. Match non-helmet riders to motorbikes using centroid distance
            violations = find_violations(tracked)
            
            # 3. Deduplication and async saving
            violation_ids_this_frame = {v.track_id for v in violations}
            
            for v in violations:
                if v.track_id not in seen_violation_ids:
                    seen_violation_ids.add(v.track_id)
                if violation_window.should_save(v.track_id):
                    # Dispatch fire-and-forget task
                    asyncio.create_task(save_violation(user, frame_bytes, v))

            # --- Step 3: Serialize and send JSON response ---
            boxes_payload = []
            for t in tracked:
                boxes_payload.append({
                    "track_id": t.track_id,
                    "class": t.class_name,
                    "bbox": t.box,
                    "conf": t.confidence,
                    "violation": t.track_id in violation_ids_this_frame
                })

            await websocket.send_json({
                "frame_id": frame_id,
                "boxes": boxes_payload,
                "violation_count": len(seen_violation_ids)
            })

    except WebSocketDisconnect:
        tracker.reset()
        print("Client disconnected cleanly")
    except Exception as e:
        print(f"WS error: {e}")
        await websocket.close(code=1011)
