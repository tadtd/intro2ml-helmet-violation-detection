FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app
COPY common ./common
COPY notification ./notification
RUN uv pip install --system ./common ./notification
EXPOSE 8003
CMD ["uvicorn", "notification.src.main:app", "--host", "0.0.0.0", "--port", "8003"]
