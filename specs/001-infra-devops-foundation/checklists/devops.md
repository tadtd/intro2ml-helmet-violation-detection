# DevOps Requirements-Quality Checklist: Infrastructure and DevOps Foundation

**Purpose**: Validate DevOps requirement clarity, completeness, consistency, and handoff readiness before task generation
**Created**: 2026-06-29
**Feature**: [spec.md](../spec.md)

## Requirement Completeness

- [ ] CHK001 Are all required infrastructure artifact paths explicitly named, including `docs/supabase-setup.md`, `docs/devops-smoke-test.md`, `k8s/README.md`, `k8s/`, and `.github/workflows/deploy.yml`? [Completeness, Plan Source Code]
- [ ] CHK002 Are the requirements clear that `k8s/` is newly created by this feature rather than an existing directory? [Completeness, Plan Project Type]
- [ ] CHK003 Are the split documentation responsibilities fully defined for Supabase setup, local smoke testing, and Kubernetes handoff? [Completeness, Plan Structure Decision]
- [ ] CHK004 Are missing schema additions for indexes and realtime enablement specified as ordered schema modules after `03_violations.sql`? [Completeness, Spec FR-002, Plan Schema Safety]
- [ ] CHK005 Are required Kubernetes artifacts complete for API, worker, Redis, optional frontend, secret placeholders, grouping, and handoff notes? [Completeness, Contract Deployment Artifacts]
- [ ] CHK006 Are CI/CD requirements complete for build, publish, deploy outline, and validation stages without requiring production rollout? [Completeness, Spec FR-012, Contract CI/CD Outline]

## Requirement Clarity

- [ ] CHK007 Is the secret handling model stated unambiguously for local `.env`, CI workload identity, GCP Secret Manager references, and Kubernetes Secret placeholders? [Clarity, Spec FR-013, Plan Constraints]
- [ ] CHK008 Is the existing `.github/deploy.yml` clearly described as empty/nonstandard and not the target workflow path? [Clarity, Plan Scale/Scope]
- [ ] CHK009 Is the target workflow path `.github/workflows/deploy.yml` stated consistently enough to prevent workflow placement ambiguity? [Clarity, Contract CI/CD Outline]
- [ ] CHK010 Are storage bucket policies precise for `videos` private and `violations` public-read, including which bucket holds which artifact type? [Clarity, Spec FR-003]
- [ ] CHK011 Is the Docker smoke-test boundary explicit that full ML inference and violation crop generation are out of scope? [Clarity, Data Model Local Runtime Runbook]
- [ ] CHK012 Are deployment boundary exclusions explicit for production rollout, DNS, TLS, GKE provisioning, Terraform, Helm, ArgoCD, and External Secrets? [Clarity, Plan Constraints]

## Requirement Consistency

- [ ] CHK013 Do secret handling requirements align across the spec, plan, data model, and deployment contract without implying External Secrets as a dependency? [Consistency, Spec CA-005, Plan Deployment Secrets]
- [ ] CHK014 Do Supabase least-privilege requirements consistently separate frontend anon/publishable usage from API/worker service-role usage? [Consistency, Spec FR-009, Constitution Principle IV]
- [ ] CHK015 Do local-first requirements consistently require Docker Compose validation before Kubernetes artifact readiness? [Consistency, Spec FR-016, Constitution Principle III]
- [ ] CHK016 Do documentation paths remain consistent across plan, data model, quickstart, and contracts after splitting the handoff docs? [Consistency, Plan Structure Decision]
- [ ] CHK017 Do Kubernetes manifest requirements align with the stated reviewable-artifact boundary rather than implying live production deployment? [Consistency, Spec FR-011, Contract Boundary]
- [ ] CHK018 Do Supabase schema ordering requirements align between the feature spec, plan, data model, and Supabase setup contract? [Consistency, Spec FR-002, Contract Supabase Setup]

## Acceptance Criteria Quality

- [ ] CHK019 Are setup-time and smoke-test-time success criteria measurable with explicit thresholds? [Measurability, Spec SC-001, Spec SC-003]
- [ ] CHK020 Can the requirement "100% of required schema steps, storage buckets, auth behavior, and realtime behavior have an explicit verification step" be traced to concrete documentation artifacts? [Acceptance Criteria, Spec SC-002]
- [ ] CHK021 Are production handoff success criteria measurable without executing an actual production deployment? [Acceptance Criteria, Spec SC-005]
- [ ] CHK022 Are reviewer criteria for finding no real secrets objectively defined by artifact types and prohibited secret classes? [Acceptance Criteria, Spec FR-015, Spec SC-004]
- [ ] CHK023 Is handoff readiness for other team members measured beyond subjective clarity, or is the 90% satisfaction criterion enough for grading? [Measurability, Spec SC-007]

## Scenario Coverage

- [ ] CHK024 Are primary developer setup, local runtime smoke-test, and infrastructure-owner handoff scenarios all covered with independent tests? [Coverage, Spec User Stories 1-3]
- [ ] CHK025 Are alternate paths documented for already-existing Supabase storage buckets and repeated schema setup attempts? [Coverage, Spec Edge Cases]
- [ ] CHK026 Are exception scenarios documented for missing local environment values, failed upload wiring, disabled realtime, and incomplete worker readiness? [Coverage, Spec Edge Cases]
- [ ] CHK027 Are requirements clear that optional frontend deployment is documented but not mandatory for API, worker, and Redis completeness? [Coverage, Spec Edge Cases]
- [ ] CHK028 Are requirements defined for running smoke tests from PowerShell on Windows, including command style and expected result descriptions? [Coverage, Quickstart]

## Rollback And Failure Documentation

- [ ] CHK029 Are rollback or recovery documentation requirements defined for failed schema additions, especially indexes and realtime enablement? [Gap, Data Model Schema Setup Sequence]
- [ ] CHK030 Are failure-mode requirements defined for partial Supabase setup where tables exist but buckets, auth, or realtime are incomplete? [Gap, Spec Edge Cases]
- [ ] CHK031 Are requirements specified for what the handoff docs must say when Kubernetes manifests cannot be applied due to missing secrets or placeholder values? [Gap, Contract Deployment Artifacts]
- [ ] CHK032 Are CI/CD failure assumptions documented for workload identity misconfiguration, image push failure, and GKE credential setup failure? [Gap, Contract CI/CD Outline]

## Dependencies And Assumptions

- [ ] CHK033 Are all non-required tools explicitly excluded so implementers do not add Terraform, Helm, ArgoCD, or External Secrets as mandatory dependencies? [Dependency Boundary, Plan Constraints]
- [ ] CHK034 Are assumptions about developer access to Supabase, local credentials, and sample upload files documented and sufficient for task planning? [Assumption, Spec Assumptions]
- [ ] CHK035 Are GCP project, Artifact Registry, GKE cluster, and secret-provider values clearly treated as placeholders or external inputs rather than committed configuration? [Dependency, Contract Deployment Artifacts]
- [ ] CHK036 Are requirements clear about which files are examples/placeholders versus runnable workflow or manifest artifacts? [Clarity, Plan Source Code]

## Handoff Readiness

- [ ] CHK037 Are the requirements sufficient for another team member to know which docs to read for Supabase setup, smoke tests, and Kubernetes deployment handoff? [Handoff, Plan Structure Decision]
- [ ] CHK038 Are reviewer expectations documented for detecting accidental real secrets across `.env`, kubeconfig, certificates, private keys, service-role keys, and workflow files? [Handoff, Spec FR-015]
- [ ] CHK039 Are the planned docs traceable to grading concerns: local reproducibility, Supabase completeness, deployment boundary, and secret safety? [Traceability, Plan Summary]
- [ ] CHK040 Are implementation exclusions documented clearly enough to prevent ML inference or frontend workflow tasks from entering this feature? [Boundary, Plan Summary]

## Implementation Review Note

Reviewed during implementation after adding `docs/supabase-setup.md`,
`docs/devops-smoke-test.md`, `k8s/README.md`, `k8s/*.yaml`, and
`.github/workflows/deploy.yml`. The remaining checklist boxes are preserved
as original requirements-quality questions, and the implementation artifacts now
document local reproducibility, Supabase setup completeness, storage bucket
policy, Docker smoke-test steps, Kubernetes deployment boundary, CI/CD
credential assumptions, rollback/failure notes, and handoff readiness.
