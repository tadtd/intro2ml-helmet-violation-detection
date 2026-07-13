# CI/CD Contract: GitHub Actions to GKE

## Trigger Contract

The deployment workflow MUST run on:

- Push to `main`
- Manual `workflow_dispatch` for redeploy/rollback operations

Pull requests SHOULD run validation steps without deploying.

## Required Workflow Stages

1. Checkout repository.
2. Install frontend dependencies and run frontend lint/build.
3. Install backend dependencies with `uv` and run backend tests.
4. Build Docker images for:
   - `frontend`
   - `auth`
   - `ingestion`
   - `dashboard`
   - `notification`
   - `orchestration`
   - `inference`
5. Authenticate to Google Cloud from the `GCP_SA_KEY` GitHub Actions secret without committing service account keys.
6. Configure Docker authentication for Artifact Registry.
7. Push images to `asia-southeast1` Artifact Registry with commit-SHA tags.
8. Render the selected Kustomize overlay with the same commit SHA.
9. Apply the overlay to the target namespace.
10. Wait for rollout status.
11. Run smoke checks.
12. Record the release SHA and mark known-good only after smoke checks pass.

## Image Tag Contract

Project images MUST use:

```text
asia-southeast1-docker.pkg.dev/<PROJECT_ID>/<REPOSITORY>/<SERVICE>:<COMMIT_SHA>
```

Rules:

- `COMMIT_SHA` is the GitHub commit that triggered the workflow.
- `latest` is not a deployable release tag.
- Third-party images such as Redis and Traefik are pinned to explicit versions.

## Environment Inputs

Manual dispatch MAY accept:

| Input | Allowed Values | Purpose |
|-------|----------------|---------|
| `environment` | `staging`, `production` | Select Kustomize overlay |
| `commit_sha` | Git SHA | Redeploy or rollback target |
| `operation` | `deploy`, `rollback`, `smoke-test` | Select workflow path |

## Required GitHub Secrets And Variables

The workflow needs one GitHub Actions secret:

- `GCP_SA_KEY`

The workflow needs these GitHub Actions variables:

- `GCP_PROJECT_ID=helmet-detection-2026`
- `GKE_REGION=asia-southeast1`
- `GKE_CLUSTER=helmet-cluster`
- `ARTIFACT_REGISTRY_REPOSITORY=helmet-repo`
- `DUCKDNS_DOMAIN=dtdat-nthv.duckdns.org`

Runtime application secrets remain in GCP Secret Manager, not GitHub secrets, unless needed only by CI validation.

## Rollback Contract

Rollback MUST:

1. Accept or discover the previous known-good commit SHA.
2. Update Kustomize image tags to that SHA.
3. Apply the target environment overlay.
4. Wait for rollout status.
5. Run smoke checks.
6. Record rollback result.

Rollback MUST NOT retag `latest`.

## Failure Handling

- If tests fail, do not build or push images.
- If image push fails, do not deploy.
- If manifest render fails, do not apply.
- If rollout fails, mark release failed and keep previous known-good SHA.
- If smoke checks fail, block demo-ready promotion and recommend rollback.
