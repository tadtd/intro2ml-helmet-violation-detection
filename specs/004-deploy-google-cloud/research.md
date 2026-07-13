# Research: Google Cloud Deployment

## Decision: Use GKE Autopilot in `asia-southeast1`

**Rationale**: GKE Autopilot removes node-pool management and supports the cost-control goal because the initial deployment pays around declared workload resource profiles instead of pre-provisioned idle nodes. `asia-southeast1` keeps the deployment close to Vietnam while using the requested Singapore region.

**Alternatives considered**:
- GKE Standard: more control, but higher idle-node cost and operational overhead for a free-trial deployment.
- Cloud Run: simpler for stateless services, but awkward for Celery workers, Redis, internal service routing, and Kubernetes-specific Traefik/cert-manager requirements.
- Single VM: cheaper to start, but loses Kubernetes parity and does not satisfy the selected GKE target.

## Decision: Kustomize base plus environment overlays

**Rationale**: Kustomize provides a native Kubernetes manifest workflow that fits one base deployment with staging/production overlays for namespaces, image tags, hostnames, secrets, and resource profiles. It avoids Helm chart complexity while staying easy for GitHub Actions to render and apply.

**Alternatives considered**:
- Raw YAML only: simple initially, but duplicates environment-specific differences.
- Helm: powerful, but extra template complexity is not justified for this first deployment.
- Helmfile/umbrella chart: too heavy for a free-trial MVP deployment.

## Decision: One GKE cluster with separate namespaces per environment

**Rationale**: Namespaces isolate staging and production-ready resources, secret bindings, release state, and access controls while avoiding the cost and setup overhead of multiple clusters.

**Alternatives considered**:
- Single namespace: cheapest and simplest, but makes staging/production separation weak.
- Separate clusters: stronger isolation, but too expensive and operationally large for the initial free-trial target.
- Namespace per service: creates noisy RBAC and discovery complexity without solving the environment boundary.

## Decision: Public traffic through one Traefik LoadBalancer

**Rationale**: A single public Traefik Service limits cloud LoadBalancer hourly cost and centralizes routing for Dashboard, Ingestion API, WebSocket status, and live stream paths. Kubernetes Services for Auth, Orchestration, Notification, Inference Worker, Redis, and Dashboard API remain ClusterIP unless explicitly routed by Traefik.

**Alternatives considered**:
- One LoadBalancer per public service: easier mental model, but unnecessary recurring cost.
- GKE Gateway/Ingress only: viable, but the project already uses Traefik locally and the user selected Traefik in-cluster.
- NodePort: poor fit for Autopilot and public demo access.

## Decision: DuckDNS plus Let's Encrypt TLS through cert-manager

**Rationale**: DuckDNS provides a free demo domain, and cert-manager can issue and renew Let's Encrypt certificates through HTTP-01 using the existing ingress path. Temporary LoadBalancer IP access is allowed only for early smoke tests, not demo or production-ready use.

**Alternatives considered**:
- No TLS: unacceptable for login/session workflows.
- Paid domain immediately: cleaner long-term, but unnecessary for the free-trial/demo goal.
- Manual certificates: fragile and not repeatable.

## Decision: GCP Secret Manager with Workload Identity Federation for GKE

**Rationale**: Workload Identity Federation lets Kubernetes workloads access Google Cloud APIs without static service account key files. Secret Manager stores Supabase connection values, JWT secrets, DuckDNS token, and deployment-only credentials outside the repository.

**Alternatives considered**:
- Committed Kubernetes Secret YAML: violates the no-secrets-in-repo requirement.
- GitHub encrypted secrets only: useful for CI, but runtime workloads still need safe access.
- Service account JSON keys mounted into pods: works, but is less secure and harder to rotate.

## Decision: In-cluster Redis StatefulSet with a small PVC

**Rationale**: Self-hosted Redis satisfies the queue/cache dependency at lower initial cost than Memorystore. A small PVC preserves Redis append-only data across pod restarts for the initial demo workload.

**Alternatives considered**:
- Memorystore: managed and safer operationally, but out of scope because of cost.
- Redis Deployment without storage: simpler, but restart behavior is weaker.
- External Redis provider: adds another billing/security surface.

## Decision: Fixed replicas before HPA

**Rationale**: Fixed replicas make Autopilot cost easier to predict under the free trial. HPA should wait until smoke tests provide enough CPU, memory, and processing-duration data to set meaningful targets.

**Alternatives considered**:
- Enable HPA immediately: better elasticity, but risks unexpected spend and bad thresholds.
- Scale everything to zero: cheaper idle posture, but not aligned with always-available demo access and stateful Redis.

## Decision: Conservative resource baseline plus larger CPU-only inference worker

**Rationale**: API and frontend services should start small for smoke tests. The inference worker needs a larger CPU/memory envelope because ONNX Runtime and OpenCV can be memory-heavy. GPU scheduling is deferred to avoid Autopilot hardware-specific billing and setup.

**Alternatives considered**:
- Tiny requests for all services: likely causes inference worker restarts and confusing failed jobs.
- High requests for all services: unnecessary free-trial spend.
- GPU-ready profile: better performance, but outside the cost-controlled initial scope.

## Decision: Commit-SHA image tags and previous-known-good SHA rollback

**Rationale**: Commit-SHA tags make each deployed image traceable and reproducible. Rollback by redeploying the previous known-good SHA avoids mutable `latest` ambiguity and works cleanly with Kustomize overlays.

**Alternatives considered**:
- `latest` only: easy, but not auditable or reproducible.
- Semantic versions only: useful for releases, but heavier than needed for main-branch CI/CD.
- Retagging `latest`: introduces mutable rollback state.

## Decision: GitHub Actions builds and deploys on main

**Rationale**: The workflow should run lint/tests/builds, authenticate to Google Cloud, push images to Artifact Registry in `asia-southeast1`, set Kustomize images to the current commit SHA, apply the staging overlay, and record the deployed SHA. Production-ready promotion can reuse the same overlay pattern after staging smoke checks pass.

**Alternatives considered**:
- Manual image build and deploy: too error-prone for repeatable release records.
- Cloud Build: good Google-native option, but the user selected GitHub Actions.
- GitOps controller: valuable later, but extra infrastructure for the first deployment.

## Decision: Budget alerts before deployment

**Rationale**: Billing alerts at 50%, 90%, and 100% of the $300 free-trial budget are a hard precondition before the cluster or load balancer is created.

**Alternatives considered**:
- Alerts after cluster creation: risks spend before safeguards.
- Manual cost checks only: too easy to miss.

## References

- GKE Autopilot overview and resource request behavior: https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-overview
- Workload Identity Federation for GKE: https://cloud.google.com/kubernetes-engine/docs/concepts/workload-identity
- Artifact Registry Docker images: https://cloud.google.com/artifact-registry/docs/docker/store-docker-container-images
- cert-manager HTTP-01 solver: https://cert-manager.io/docs/configuration/acme/http01/
