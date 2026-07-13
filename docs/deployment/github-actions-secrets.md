# GitHub Actions Configuration

Use repository or environment variables for non-secret deployment identifiers.

## Required Variables

- `GCP_PROJECT_ID=helmet-detection-2026`
- `GKE_REGION=asia-southeast1`
- `GKE_CLUSTER=helmet-cluster`
- `ARTIFACT_REGISTRY_REPOSITORY=helmet-repo`
- `DUCKDNS_DOMAIN=dtdat-nthv.duckdns.org`
- `LETSENCRYPT_EMAIL=<your-email-address>`

## Required Secrets

- `GCP_SA_KEY`

## Runtime Secrets

Runtime application secrets belong in GCP Secret Manager, not GitHub secrets.

`GCP_SA_KEY` is the JSON key for the deploy service account. Keep it in GitHub Actions secrets only; do not commit it to the repository.
