# Data Model: Google Cloud Deployment

## Cloud Environment

Represents a GKE-hosted runtime environment.

**Fields**
- `name`: `staging` or `production`
- `namespace`: Kubernetes namespace name, unique per environment
- `region`: `asia-southeast1`
- `clusterName`: GKE Autopilot cluster name
- `publicHost`: DuckDNS hostname for demo/production-ready use
- `temporaryLoadBalancerIp`: optional early smoke-test address
- `status`: `not_created`, `provisioning`, `ready`, `degraded`, `blocked`, `destroyed`
- `budgetAlertsReady`: boolean, must be true before deployment
- `createdAt`, `updatedAt`: timestamps

**Relationships**
- Has many `GKEWorkload` records
- Has one or more `Release` records
- Has many `SmokeCheckResult` records
- Has one `PublicEndpoint` for external application traffic

**Validation Rules**
- `budgetAlertsReady` must be true before creating cloud runtime resources.
- Demo/production-ready status requires `publicHost`, valid TLS, and no temporary-only endpoint.
- Environment namespace must be unique inside the cluster.

## Release

Represents a deployed commit-SHA version of the system.

**Fields**
- `releaseId`: unique release identifier
- `environment`: target `CloudEnvironment`
- `commitSha`: full or short Git commit SHA used for all images
- `imageRegistry`: Artifact Registry repository path in `asia-southeast1`
- `serviceImages`: map of service name to image digest/tag
- `deployedAt`: timestamp
- `deployedBy`: GitHub Actions actor or maintainer
- `status`: `pending`, `deploying`, `smoke_testing`, `passed`, `failed`, `rolled_back`
- `knownGood`: boolean
- `rollbackTargetSha`: previous known-good SHA when available

**Relationships**
- Belongs to one `CloudEnvironment`
- Produces many `GKEWorkload` image revisions
- Has many `SmokeCheckResult` records

**State Transitions**
`pending -> deploying -> smoke_testing -> passed`
`pending -> deploying -> failed`
`passed -> rolled_back` when replaced by rollback

**Validation Rules**
- `commitSha` is required; mutable `latest` is not a valid release identity.
- A release can become `knownGood` only after smoke checks pass.
- Rollback can target only a previous `knownGood` SHA.

## Deployment Configuration

Represents environment-specific configuration required to deploy and run services.

**Fields**
- `environment`: target environment
- `kustomizeOverlayPath`: path such as `deploy/k8s/overlays/staging`
- `secretManagerProject`: GCP project containing runtime secrets
- `secretNames`: approved Secret Manager names
- `serviceAccountBindings`: map of Kubernetes service account to IAM principal/roles
- `supabaseUrlRef`, `supabaseAnonKeyRef`, `supabaseServiceRoleRef`, `supabaseJwtSecretRef`: Secret Manager references
- `duckDnsTokenRef`: Secret Manager reference
- `resourceProfileRef`: selected `ResourceProfile`

**Relationships**
- Belongs to one `CloudEnvironment`
- References many `SecretBinding` records
- Selects one or more `ResourceProfile` records

**Validation Rules**
- No plaintext secret values are allowed in Git-tracked files.
- Secret access must be scoped through workload identity and least-privilege IAM roles.
- Overlay must render successfully before apply.

## GKE Workload

Represents a deployable application component.

**Fields**
- `name`: `frontend`, `ingestion`, `auth`, `orchestration`, `notification`, `dashboard`, `inference-worker`, `realtime-stream`, `redis`, or `traefik`
- `kind`: `Deployment`, `StatefulSet`, or `Service`
- `exposure`: `public`, `internal`, or `ingress-routed`
- `replicas`: integer fixed count for initial deployment
- `image`: commit-SHA-tagged image except third-party images
- `ports`: container/service ports
- `healthPath`: HTTP health path when applicable
- `resourceProfile`: selected CPU/memory profile
- `serviceAccount`: Kubernetes service account
- `status`: `pending`, `healthy`, `degraded`, `failed`

**Relationships**
- Belongs to one `CloudEnvironment`
- Uses one `ResourceProfile`
- May use multiple `SecretBinding` records
- Public/routed workloads connect through `IngressRoute`

**Validation Rules**
- Dashboard and Ingestion API may be public through Traefik.
- Auth, Orchestration, Notification, Inference Worker, Redis, and internal Dashboard API remain ClusterIP unless routed by an approved ingress rule.
- Inference Worker must use the larger CPU-only resource profile.

## Resource Profile

Defines requested and maximum compute resources.

**Fields**
- `name`: `light-api`, `frontend`, `redis-small`, `inference-cpu`, `traefik-small`
- `cpuRequest`, `cpuLimit`: Kubernetes CPU values
- `memoryRequest`, `memoryLimit`: Kubernetes memory values
- `ephemeralStorageRequest`: optional
- `tuningStatus`: `initial`, `reviewed`, `adjusted`
- `lastReviewedAt`: timestamp

**Relationships**
- Used by many `GKEWorkload` records
- Reviewed through `SmokeCheckResult` metrics

**Validation Rules**
- Initial requests must be conservative for low-traffic services.
- Inference Worker profile must be reviewed after smoke tests for ONNX/OpenCV memory behavior.
- HPA settings are not part of initial profiles.

## Public Endpoint

Represents external user access.

**Fields**
- `host`: DuckDNS hostname
- `tlsIssuer`: Let's Encrypt issuer name
- `certificateStatus`: `pending`, `valid`, `failed`, `expired`
- `loadBalancerIp`: Traefik Service external IP
- `routes`: list of Dashboard, Ingestion API, WebSocket status, and camera-stream paths
- `demoReady`: boolean

**Relationships**
- Belongs to one `CloudEnvironment`
- Served by Traefik `IngressRoute`
- Uses cert-manager certificate resources

**Validation Rules**
- `demoReady` requires a DuckDNS host and valid TLS certificate.
- Temporary LoadBalancer IP access is allowed only for early development smoke tests.

## Secret Binding

Represents access from a Kubernetes workload identity to a GCP Secret Manager secret.

**Fields**
- `secretName`: GCP Secret Manager secret name
- `consumerServiceAccount`: Kubernetes service account
- `iamRole`: expected `Secret Manager Secret Accessor`
- `environment`: target environment
- `rotationRequired`: boolean
- `lastValidatedAt`: timestamp

**Relationships**
- Belongs to one `DeploymentConfiguration`
- Used by one or more `GKEWorkload` records

**Validation Rules**
- Secret values must not be printed in CI logs or application logs.
- Each binding must be environment-scoped where possible.
- Service account keys are not allowed.

## Ingress Route

Represents an externally reachable route through Traefik.

**Fields**
- `routeName`: unique route name
- `host`: DuckDNS hostname
- `pathPrefix`: public path
- `targetService`: Kubernetes Service name
- `targetPort`: service port
- `tlsEnabled`: boolean
- `exposureApproved`: boolean

**Relationships**
- Belongs to one `PublicEndpoint`
- Targets one public or ingress-routed `GKEWorkload`

**Validation Rules**
- Only approved public paths may be routed externally.
- Auth, Orchestration, Notification, and Inference Worker must not get direct public routes.

## Operational Alert

Represents a cost, health, quota, or processing alert.

**Fields**
- `alertType`: `budget`, `health`, `quota`, `processing_failure`, `certificate`
- `threshold`: numeric or status threshold
- `severity`: `info`, `warning`, `critical`
- `recipient`: maintainer contact group
- `status`: `configured`, `triggered`, `acknowledged`, `resolved`

**Relationships**
- Belongs to one `CloudEnvironment`
- May reference a `GKEWorkload`, `PublicEndpoint`, or `Release`

**Validation Rules**
- Budget alerts at 50%, 90%, and 100% are required before deployment.
- Critical alerts must identify an owner or maintainer group.

## Smoke Check Result

Represents a post-deployment validation run.

**Fields**
- `checkId`: unique identifier
- `environment`: target environment
- `releaseCommitSha`: release under test
- `startedAt`, `finishedAt`: timestamps
- `checks`: map of check name to pass/fail
- `metrics`: CPU, memory, restart count, processing duration, login latency
- `status`: `passed`, `failed`, `blocked`
- `notes`: optional investigation notes

**Relationships**
- Belongs to one `Release`
- Reviews many `GKEWorkload` records

**Validation Rules**
- A release cannot be marked known-good until required smoke checks pass.
- Failed smoke checks must block demo-ready promotion.

## Known-Good SHA

Represents the rollback target.

**Fields**
- `commitSha`: deployed commit SHA
- `environment`: target environment
- `releaseId`: associated release
- `validatedAt`: timestamp of passing smoke checks
- `rollbackEligible`: boolean

**Relationships**
- Points to one `Release`
- Used by rollback scripts and CI/CD workflow dispatch

**Validation Rules**
- Must reference a release with passing smoke checks.
- Must remain available in Artifact Registry.
