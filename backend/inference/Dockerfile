FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app
COPY common ./common
COPY inference ./inference
RUN uv pip install --system ./common ./inference
CMD ["celery", "-A", "inference.src.worker.celery_app", "worker", "-Q", "inference", "--loglevel=info"]
