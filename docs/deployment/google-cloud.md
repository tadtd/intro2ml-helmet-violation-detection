# Google Cloud Deployment

This deployment targets a low-cost GKE Autopilot environment for the helmet violation detection system.

## Scope

- Region: `asia-southeast1`
- Cluster mode: GKE Autopilot
- Namespaces: `helmet-staging` and `helmet-production`
- Public entrypoint: Traefik through one `LoadBalancer` Service
- Demo/production URL: DuckDNS subdomain with Let's Encrypt TLS via cert-manager
- Runtime secrets: GCP Secret Manager accessed through Workload Identity Federation for GKE
- Images: Artifact Registry in `asia-southeast1`, tagged by commit SHA
- Redis: in-cluster StatefulSet with a small persistent volume
- Autoscaling: deferred; fixed replicas are used initially

## Implementation Order

1. Configure budget alerts before creating cloud runtime resources.
2. Create Artifact Registry and GKE Autopilot resources.
3. Create required Secret Manager entries and Workload Identity bindings.
4. Render Kustomize overlays locally.
5. Deploy staging through GitHub Actions or manual `kubectl apply -k`.
6. Validate DuckDNS, TLS, public routes, internal-only services, and smoke checks.
7. Record the passing commit SHA as known-good.
8. Promote production-ready overlay only after staging passes.

## Owners

- Deployment owner: project maintainer
- Secrets owner: project maintainer with GCP IAM access
- Release owner: GitHub Actions deploy service account
- Incident owner: maintainer running `deploy/scripts/win/inspect-health.ps1`

## Owner Checklist

- [ ] Budget alerts were verified with `deploy/scripts/win/validate-budget-alerts.ps1`.
- [ ] Secret Manager entries were created with `deploy/scripts/win/create-secret-manager-secrets.ps1`.
- [ ] Workload Identity bindings were configured with `deploy/scripts/win/configure-workload-identity.ps1`.
- [ ] Staging and production overlays render with `deploy/scripts/win/validate-manifests.ps1`.
- [ ] Public exposure is limited with `deploy/scripts/win/validate-exposure.ps1`.
- [ ] Secrets scan passes with `deploy/scripts/win/scan-secrets.ps1`.
- [ ] Smoke checks pass with `deploy/scripts/win/smoke-test.ps1`.
- [ ] Rollback has been tested with `deploy/scripts/win/rollback.ps1`.

## Key References

- Plan: `specs/004-deploy-google-cloud/plan.md`
- Contracts: `specs/004-deploy-google-cloud/contracts/`
- Quickstart: `specs/004-deploy-google-cloud/quickstart.md`
- Deployment manifests: [deploy/k8s/](file:///e:/hcmus/semester-6/intro2ml-helmet-violation-detection/deploy/k8s/)
