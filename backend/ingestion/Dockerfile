FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app
COPY common ./common
COPY ingestion ./ingestion
RUN uv pip install --system ./common ./ingestion
EXPOSE 8002
CMD ["uvicorn", "ingestion.src.main:app", "--host", "0.0.0.0", "--port", "8002"]
