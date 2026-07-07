import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from common.config import get_settings
from .db.profiles import upsert_profile
from .grpc_server import serve_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth.api")

settings = get_settings()


class RegisterRequest(BaseModel):
    user_id: str
    full_name: str
    role: str = "operator"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start gRPC server in the background
    grpc_task = asyncio.create_task(serve_grpc(50051))
    logger.info("Background gRPC server task started")
    yield
    # Shutdown gRPC server
    grpc_task.cancel()
    try:
        await grpc_task
    except asyncio.CancelledError:
        logger.info("Background gRPC server task cancelled successfully")


app = FastAPI(title="Auth Microservice", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/register")
def register_user(req: RegisterRequest) -> dict[str, str]:
    """Helper endpoint to register or upsert a user profile locally."""
    try:
        upsert_profile(user_id=req.user_id, full_name=req.full_name, role=req.role)
        return {"status": "ok", "message": "Profile upserted"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "auth"}
