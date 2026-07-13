# Secret Management

Runtime secrets are stored in GCP Secret Manager and accessed from GKE through Workload Identity Federation.

## Required Secrets

- `helmet-supabase-url`
- `helmet-supabase-anon-key`
- `helmet-supabase-service-role-key`
- `helmet-supabase-jwt-secret`
- `helmet-supabase-video-bucket`
- `helmet-supabase-storage-bucket`
- `helmet-duckdns-token`
- `helmet-jwt-secret`

## Rules

- Do not commit plaintext secret values.
- Do not mount service account JSON keys.
- Bind Kubernetes service accounts only to the secrets they require.
- Rotate secrets through Secret Manager versions.
- Re-run smoke checks after rotation.
