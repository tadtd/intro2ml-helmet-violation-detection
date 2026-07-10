import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.config import get_settings
from .middleware import GrpcAuthMiddleware
from .queries import router as query_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dashboard.main")

settings = get_settings()

app = FastAPI(title="Dashboard Query Microservice")

# Apply the gRPC authentication middleware to secure all query endpoints
# For local Docker, the auth service address is auth:50051
app.add_middleware(GrpcAuthMiddleware, auth_service_addr="auth:50051")

# Keep CORS outermost so auth errors returned by GrpcAuthMiddleware still include
# Access-Control-Allow-* headers for the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include query router
app.include_router(query_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "dashboard"}
