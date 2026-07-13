# Production Overlay

Use this overlay only after staging smoke checks pass.

Required replacements before deployment:

- `PROJECT_ID`
- `PRODUCTION_PROJECT_ID`
- `REPOSITORY`
- `COMMIT_SHA`
- `yourname.duckdns.org`
- `maintainer@example.com`

Render:

```bash
kubectl kustomize deploy/k8s/overlays/production
```
