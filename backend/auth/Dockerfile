FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app
COPY common ./common
COPY auth ./auth
RUN uv pip install --system ./common ./auth
EXPOSE 8001
EXPOSE 50051
CMD ["uvicorn", "auth.src.main:app", "--host", "0.0.0.0", "--port", "8001"]
