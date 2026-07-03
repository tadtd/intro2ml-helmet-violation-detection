FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app
COPY common ./common
COPY orchestration ./orchestration
RUN uv pip install --system ./common ./orchestration
# Command will be overridden in docker-compose for worker/daemon
CMD ["python", "-m", "orchestration.src.retention"]
