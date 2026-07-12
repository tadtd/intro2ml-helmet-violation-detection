# Contract: Deployment Artifacts

## Kubernetes Manifest Set

The `k8s/` directory does not exist yet. This feature creates it for reviewable
GKE handoff artifacts.

| File | Required Contents |
|------|-------------------|
| `k8s/README.md` | GKE handoff notes, secret creation guidance, and review steps |
| `k8s/namespace.yaml` | Namespace placeholder for the app |
| `k8s/redis.yaml` | Redis Deployment/Service for queue dependency |
| `k8s/api.yaml` | API Deployment/Service with image placeholder and secret refs |
| `k8s/worker.yaml` | Worker Deployment with image placeholder and secret refs |
| `k8s/frontend.yaml` | Optional frontend Deployment/Service with image placeholder |
| `k8s/secrets.example.yaml` | Placeholder secret names only, no values |
| `k8s/kustomization.yaml` | Manifest grouping for review/apply flow |

## CI/CD Outline

The GitHub Actions workflow outline must be created at
`.github/workflows/deploy-gke.yml`. The existing `.github/deploy.yml` is
currently empty/nonstandard and is not the target workflow path.

The workflow outline must cover:

1. Authenticate to GCP through workload identity or documented placeholders.
2. Build API and worker images.
3. Optionally build frontend image.
4. Push images to Artifact Registry.
5. Configure GKE credentials.
6. Apply or render Kubernetes manifests.
7. Run a post-deploy health validation command.

## Secret Contract

- No real secret values in YAML.
- Secret names are placeholders, GCP Secret Manager references, or documented
  Kubernetes Secret placeholder names.
- Workload identity is the preferred CI authentication mechanism.
- Kubernetes Secret placeholders are allowed only with documented creation
  steps.
- Terraform, Helm, ArgoCD, and External Secrets are not required dependencies.

## Boundary

These artifacts are reviewable and non-executing by default. Actual production
rollout, DNS, TLS, GKE provisioning, and environment-specific values are outside
this feature.
