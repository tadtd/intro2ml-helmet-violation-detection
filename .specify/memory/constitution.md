<!--
Sync Impact Report
Version change: N/A -> 1.0.0
Modified principles:
- Template placeholder -> I. Secret Hygiene Is Mandatory
- Template placeholder -> II. Infrastructure Changes Require Local Runbooks
- Template placeholder -> III. Local-First Runtime
- Template placeholder -> IV. Supabase Least Privilege
- Template placeholder -> V. Ordered, Non-Destructive Schema Changes
- Template placeholder -> VI. Kubernetes and CI/CD Secret Isolation
- Template placeholder -> VII. Repository-Fit Artifacts
Added sections:
- Security and Infrastructure Constraints
- Development Workflow and Quality Gates
Removed sections:
- None
Templates requiring updates:
- Updated: .specify/templates/plan-template.md
- Updated: .specify/templates/spec-template.md
- Updated: .specify/templates/tasks-template.md
- Not present: .specify/templates/commands/*.md
- Updated: README.md
Follow-up TODOs:
- None
-->
# Helmet Violation Detection Constitution

## Core Principles

### I. Secret Hygiene Is Mandatory
Real secrets MUST NOT be committed. This includes tokens, service role keys,
real `.env` files, kubeconfigs, certificates, private keys, and equivalent
credentials. Only documented placeholders, examples, or local-only dummy values
may be stored in the repository.

Rationale: the system integrates with Supabase, CI/CD, and deployment targets
where a leaked credential can expose user data, storage objects, or production
infrastructure.

### II. Infrastructure Changes Require Local Runbooks
Every change to Docker Compose, Kubernetes, CI/CD, Supabase infrastructure,
Redis, API, worker, or related deployment configuration MUST document how to run
it locally and how to perform a local smoke test.

Rationale: infrastructure that cannot be reproduced and checked locally is too
risky for a course project with multiple moving parts.

### III. Local-First Runtime
Docker Compose MUST run Redis, the FastAPI API, and the Celery worker
successfully before Kubernetes deployment work is considered ready. Kubernetes
manifests, cloud deployment, and CI/CD automation MUST build on the proven local
Compose path.

Rationale: the API, worker, Redis queue, and ML processing flow form the minimum
runtime backbone. Debugging that backbone locally is required before adding
cluster complexity.

### IV. Supabase Least Privilege
Frontend code MUST use only publishable or anon Supabase keys. Backend services,
workers, migrations, and trusted administrative tooling MAY use the service role
key only through environment variables or a secret manager. Service role keys
MUST NOT appear in browser bundles, public config, or committed files.

Rationale: Supabase service role keys bypass Row Level Security and must remain
server-side only.

### V. Ordered, Non-Destructive Schema Changes
Supabase schema files and migrations MUST have a clear execution order. Schema
changes SHOULD be idempotent where practical and MUST avoid destructive changes
to existing data unless a documented migration and rollback plan exists.

Rationale: violation evidence, video metadata, profiles, and audit-relevant
rows must remain stable as the data model evolves.

### VI. Kubernetes and CI/CD Secret Isolation
Kubernetes manifests and CI/CD workflows MUST NOT hardcode secrets. They MUST use
a documented secret manager integration or secret placeholders with documented
commands or steps for creating the required secrets.

Rationale: deployment artifacts are often copied between environments, so secret
material must stay outside the repository and outside static manifests.

### VII. Repository-Fit Artifacts
Generated artifacts MUST fit the current repository structure. Work MUST extend
the existing `backend/`, `frontend/`, `models/`, `crawl/`, `docs/`, `.specify/`,
and deployment paths as appropriate, and MUST NOT create a new monorepo or
parallel project scaffold for the same system.

Rationale: duplicating the project structure makes implementation, review, and
deployment harder and risks diverging from the plan for this course project.

## Security and Infrastructure Constraints

- `.env.example` files MAY contain empty values or documented placeholders only.
- Local setup documentation MUST identify required environment variables without
  embedding real secret values.
- Infrastructure documentation MUST include at least one smoke test that proves
  Redis, API, and worker are reachable or running for local Compose changes.
- Supabase schema updates MUST state the intended order of execution.
- Kubernetes and CI/CD changes MUST document how required secrets are created or
  injected outside source control.

## Development Workflow and Quality Gates

- Feature plans MUST pass a Constitution Check before implementation research
  and again after design.
- Feature specs that touch infrastructure, Supabase, auth, CI/CD, Kubernetes, or
  generated artifacts MUST include requirements that map to the relevant
  constitutional principles.
- Task lists MUST include documentation and local smoke-test tasks whenever they
  include infrastructure changes.
- Reviews MUST reject changes that expose secrets, bypass Supabase least
  privilege, skip ordered migrations, or create a parallel repository structure.
- Local Docker Compose validation is the required first deployment gate for
  Redis, API, and worker changes.

## Governance

This constitution supersedes conflicting development practices for this
repository. Amendments MUST be recorded in `.specify/memory/constitution.md`,
include a Sync Impact Report, update affected templates or runtime guidance, and
use semantic versioning.

Versioning policy:
- MAJOR: backward-incompatible governance changes or principle removals.
- MINOR: new principles, new required sections, or materially expanded guidance.
- PATCH: clarifications, wording fixes, or non-semantic refinements.

Compliance review is required for every feature plan, generated task list, and
infrastructure-related change. If a change cannot satisfy a principle, the plan
MUST document the violation, why it is necessary, and the simpler compliant
alternative that was rejected.

**Version**: 1.0.0 | **Ratified**: 2026-06-29 | **Last Amended**: 2026-06-29
