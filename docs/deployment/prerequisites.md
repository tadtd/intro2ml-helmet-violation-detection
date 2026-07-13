# Deployment Prerequisites

Complete these before applying manifests.

- [ ] GCP billing is enabled.
- [ ] Budget alerts exist at 50%, 90%, and 100% of the $300 free-trial budget.
- [ ] GKE, Artifact Registry, Secret Manager, IAM, and Cloud Billing APIs are enabled.
- [ ] GKE Autopilot cluster exists in `asia-southeast1`.
- [ ] Artifact Registry Docker repository exists in `asia-southeast1`.
- [ ] GitHub Actions Workload Identity Federation provider exists.
- [ ] Deploy service account can push Artifact Registry images and deploy to GKE.
- [ ] Secret Manager entries listed in `docs/deployment/environment-inventory.md` exist.
- [ ] DuckDNS subdomain exists.
- [ ] `kubectl` can access the target cluster.
- [ ] `kubectl kustomize deploy/k8s/overlays/staging` renders successfully.
