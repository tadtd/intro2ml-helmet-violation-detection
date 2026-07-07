import asyncio
import json
import logging
from contextlib import asynccontextmanager
import redis.asyncio as aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from common.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notification.main")

settings = get_settings()

# Store active websocket connections
active_connections: list[WebSocket] = []


async def broadcast(message: dict):
    logger.info(f"Broadcasting message: {message}")
    dead_connections = []
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send to socket: {e}")
            dead_connections.append(connection)
            
    for dead in dead_connections:
        if dead in active_connections:
            active_connections.remove(dead)


async def redis_listener():
    logger.info("Starting Redis listener for pub-sub channels")
    try:
        r = aioredis.from_url(settings.redis_url)
        pubsub = r.pubsub()
        await pubsub.subscribe("violation_detected", "job_status_update")
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                channel = message["channel"].decode("utf-8")
                data = json.loads(message["data"].decode("utf-8"))
                logger.info(f"Received message from Redis channel {channel}: {data}")
                
                if channel == "violation_detected":
                    # Map to the format expected by useWebSocketStatus: new_violation_alert
                    payload = {
                        "event": "new_violation_alert",
                        "label": data.get("label", "non-helmet"),
                        "confidence": data.get("confidence", 0.0),
                        "violationId": data.get("violationId"),
                        "videoId": data.get("videoId"),
                        "timestamp": data.get("timestamp")
                    }
                    await broadcast(payload)
                elif channel == "job_status_update":
                    payload = {
                        "event": "job_status_update",
                        "jobId": data.get("jobId"),
                        "status": data.get("status"),
                        "fileName": data.get("fileName"),
                        "completedAt": data.get("completedAt"),
                        "error": data.get("error")
                    }
                    await broadcast(payload)
                    
    except asyncio.CancelledError:
        logger.info("Redis listener cancelled, shutting down")
    except Exception as exc:
        logger.error(f"Error in Redis listener: {exc}")
        # Retry logic
        await asyncio.sleep(5)
        asyncio.create_task(redis_listener())


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Redis listener task
    listener_task = asyncio.create_task(redis_listener())
    yield
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Notification Microservice", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws/status")
async def status_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"New client connected to /ws/status. Total: {len(active_connections)}")
    try:
        while True:
            # Keep socket alive, discard incoming messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"Client disconnected from /ws/status. Total: {len(active_connections)}")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "notification"}
