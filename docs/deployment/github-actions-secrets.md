# GitHub Actions Configuration

Use repository or environment variables for non-secret deployment identifiers.

## Required Variables

- `GCP_PROJECT_ID`
- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_DEPLOY_SERVICE_ACCOUNT`
- `GKE_CLUSTER`
- `GKE_REGION`
- `ARTIFACT_REGISTRY_REPOSITORY`
- `DUCKDNS_DOMAIN`

## Runtime Secrets

Runtime application secrets belong in GCP Secret Manager, not GitHub secrets.

GitHub Actions may need only deployment identity configuration. Avoid service account JSON keys; prefer Workload Identity Federation.
