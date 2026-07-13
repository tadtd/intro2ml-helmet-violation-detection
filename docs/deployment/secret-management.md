# Secret Management

Runtime secrets are stored in GCP Secret Manager and synced into the target Kubernetes namespace during deployment.

## Required Secrets

- `helmet-supabase-url`
- `helmet-supabase-anon-key`
- `helmet-supabase-service-role-key`
- `helmet-supabase-jwt-secret`
- `helmet-supabase-video-bucket`
- `helmet-supabase-storage-bucket`
- `helmet-duckdns-token`

## Rules

- Do not commit plaintext secret values.
- Do not mount service account JSON keys.
- Rotate secrets through Secret Manager versions.
- Re-run smoke checks after rotation.
