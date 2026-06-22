from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routes import camera, videos, violations

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(videos.router)
app.include_router(violations.router)
app.include_router(camera.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
