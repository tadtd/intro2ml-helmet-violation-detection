# Rollback And Recovery

Rollback redeploys the previous known-good commit SHA.

## Procedure

1. Identify the previous known-good SHA.
2. Run the GitHub Actions workflow with `operation=rollback` and the target SHA, or run `deploy/scripts/win/rollback.ps1`.
3. Wait for rollout status.
4. Run smoke checks.
5. Record the rollback result.

## Incident Checks

- Pod status and restart counts
- Recent events
- Service endpoints
- Traefik route status
- Certificate status
- Running image SHA
- Inference processing duration
