# Staging Overlay

Use this overlay for smoke tests and demo preparation.

Required replacements before deployment:

- `PROJECT_ID`
- `STAGING_PROJECT_ID`
- `REPOSITORY`
- `COMMIT_SHA`
- `yourname.duckdns.org`
- `maintainer@example.com`

Render:

```bash
kubectl kustomize deploy/k8s/overlays/staging
```
