import asyncio
import cv2
import numpy as np
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("ingestion.websocket")
router = APIRouter()


@router.websocket("/ws/camera")
async def camera_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    logger.info("Live camera WS connection accepted")
    try:
        # We simulate a 15 FPS traffic camera
        frame_idx = 0
        h, w = 360, 640
        
        while True:
            # Create a mock frame of a road
            frame = np.zeros((h, w, 3), dtype=np.uint8)
            # Draw road background (gray)
            cv2.rectangle(frame, (100, 0), (540, h), (40, 40, 40), -1)
            # Draw lane dividers (moving dashed lines)
            dash_offset = (frame_idx * 10) % 80
            for y in range(-80 + dash_offset, h, 80):
                cv2.rectangle(frame, (315, y), (325, y + 40), (255, 255, 255), -1)

            # Draw a simulated motorcycle moving down the road
            moto_y = 50 + (frame_idx * 4) % (h - 100)
            moto_x = 240 + int(20 * np.sin(frame_idx * 0.05))
            
            # Motorbike body (blue)
            cv2.rectangle(frame, (moto_x, moto_y + 20), (moto_x + 30, moto_y + 60), (255, 100, 50), -1)
            # Rider body/head (greenish-yellow)
            cv2.circle(frame, (moto_x + 15, moto_y + 10), 10, (50, 220, 240), -1)

            # Draw bounding box labels to show it's being "detected" live
            # Motorbike Box: (moto_x - 10, moto_y + 10, moto_x + 40, moto_y + 65)
            # Violator Box (non-helmet head): (moto_x + 2, moto_y - 2, moto_x + 28, moto_y + 22)
            
            # Motorbike box (green)
            cv2.rectangle(frame, (moto_x - 10, moto_y + 10), (moto_x + 40, moto_y + 65), (0, 255, 0), 2)
            cv2.putText(frame, "motorbike: 95%", (moto_x - 10, moto_y + 5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

            # Non-helmet head box (red)
            cv2.rectangle(frame, (moto_x + 2, moto_y - 2), (moto_x + 28, moto_y + 22), (0, 0, 255), 2)
            cv2.putText(frame, "non-helmet: 89%", (moto_x + 2, moto_y - 7), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
            
            # Watermark text for live camera simulation
            cv2.putText(frame, f"LIVE CAMERA (15 FPS) - FRAME {frame_idx}", (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

            # Encode to JPEG
            success, encoded_img = cv2.imencode(".jpg", frame)
            if success:
                # Send binary image JPEG frame
                await websocket.send_bytes(encoded_img.tobytes())
                
            frame_idx += 1
            # Sleep 1/15 seconds to stream at exactly 15 FPS
            await asyncio.sleep(1.0 / 15.0)

    except WebSocketDisconnect:
        logger.info("Live camera WS connection disconnected")
    except Exception as exc:
        logger.error(f"Error in live camera WS loop: {exc}")
