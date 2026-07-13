# Artifact Registry

Container images are stored in Artifact Registry in `asia-southeast1`.

## Repository Format

```text
asia-southeast1-docker.pkg.dev/<PROJECT_ID>/<REPOSITORY>/<SERVICE>:<COMMIT_SHA>
```

## Service Image Names

| Service | Image |
|---------|-------|
| Frontend | `frontend` |
| Auth | `auth` |
| Ingestion | `ingestion` |
| Dashboard API | `dashboard` |
| Notification | `notification` |
| Orchestration | `orchestration` |
| Inference Worker / Realtime Stream | `inference` |

## Rules

- Use commit SHA tags for project images.
- Do not deploy `latest`.
- Keep third-party images pinned to explicit versions such as `redis:7-alpine` and `traefik:v3.6`.
- Rollback redeploys a previous known-good commit SHA.
