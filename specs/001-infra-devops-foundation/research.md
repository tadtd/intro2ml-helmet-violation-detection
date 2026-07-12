# Research: Infrastructure and DevOps Foundation

## Decision: Keep Docker Compose as the local runtime gate

**Rationale**: The existing `docker-compose.yml` already defines Redis, API, and
worker services. Using it as the mandatory first gate satisfies the constitution
and avoids introducing Kubernetes debugging before the local runtime is proven.

**Alternatives considered**:
- Run services manually with separate commands. Rejected because it does not
  validate the Compose path required by the constitution.
- Validate directly on GKE. Rejected because local-first validation is mandatory.

## Decision: Add ordered Supabase schema modules for indexes and realtime

**Rationale**: Existing schema files are numbered through `03_violations.sql`.
Appending `04_indexes.sql` and `05_realtime.sql` preserves ordering, avoids
rewriting existing schema files unnecessarily, and makes future setup steps
easy to document.

**Alternatives considered**:
- Edit existing schema modules. Rejected because append-only files are easier to
  review and safer for existing data.
- Use a single unnumbered migration file. Rejected because it weakens execution
  ordering.

## Decision: Document storage buckets outside SQL migrations

**Rationale**: Supabase storage bucket creation and policies are often managed
through dashboard, CLI, or admin API. The implementation should document the
decision clearly: `videos` private and `violations` public-read for evidence
crops, with verification steps.

**Alternatives considered**:
- Encode storage bucket creation only in SQL. Rejected because storage setup can
  vary by Supabase tooling and may require service privileges.
- Keep bucket visibility unspecified. Rejected because it affects frontend and
  backend access behavior.

## Decision: Scope local smoke tests to health, authenticated upload, storage
and row verification, and worker process readiness

**Rationale**: This proves infrastructure wiring without requiring model
weights, full inference, or frontend workflow implementation.

**Alternatives considered**:
- Require full violation crop generation. Rejected because ML inference is out
  of scope for this feature.
- Only test health endpoint. Rejected because it does not prove Supabase upload
  wiring.

## Decision: Use service-role credentials only in API and worker contexts

**Rationale**: Supabase service-role keys bypass row-level security and must not
be available to frontend code. Frontend keys are limited to anon/publishable
auth/session use.

**Alternatives considered**:
- Allow frontend direct writes. Rejected because it increases RLS and storage
  policy complexity for this infrastructure feature.
- Use anon credentials in backend only. Rejected because current backend DB and
  storage write paths are service-owned.

## Decision: Generate reviewable GKE manifests and CI/CD outline, not rollout

**Rationale**: The feature must prepare production artifacts but explicitly
excludes actual production deployment, DNS, TLS, and environment-specific
provisioning. The CI/CD outline belongs at `.github/workflows/deploy-gke.yml`.
The existing `.github/deploy.yml` is currently empty/nonstandard and is not the
workflow target.

**Alternatives considered**:
- Fully runnable production workflow. Rejected because it would require real
  project IDs, cluster names, and secret setup.
- Documentation only. Rejected because the feature requires manifests under
  `k8s/`.

## Decision: Prefer workload identity and documented GCP/Kubernetes secret inputs

**Rationale**: GitHub Actions workload identity avoids long-lived cloud keys in
GitHub secrets. Cluster workloads should consume GCP Secret Manager references
or documented Kubernetes Secret placeholders. This does not require the External
Secrets operator.

**Alternatives considered**:
- Store long-lived cloud keys as GitHub secrets. Rejected due to higher rotation
  and leakage risk.
- Hardcode Kubernetes Secret values. Rejected by the constitution.
- Require Terraform, Helm, ArgoCD, or External Secrets. Rejected because the
  grading handoff only requires reviewable manifests, runbooks, and a workflow
  outline.

## Decision: Split handoff documentation by audience

**Rationale**: Supabase setup, local smoke testing, and Kubernetes handoff have
different readers and validation steps. The feature will use
`docs/supabase-setup.md`, `docs/devops-smoke-test.md`, and `k8s/README.md`
instead of one combined infrastructure document.

**Alternatives considered**:
- Single combined infrastructure document. Rejected because it is less useful for the
  grading handoff and mixes local, Supabase, and GKE concerns.
- Put all guidance in `README.md`. Rejected because the detailed infrastructure
  runbooks would make the root README too broad.
