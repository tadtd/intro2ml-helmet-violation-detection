# Manifest Contract: Kustomize Layout

## Required Directory Layout

```text
deploy/k8s/
├── base/
│   ├── namespace/
│   ├── serviceaccounts/
│   ├── workloads/
│   ├── services/
│   ├── redis/
│   ├── traefik/
│   ├── cert-manager/
│   ├── secrets/
│   └── kustomization.yaml
└── overlays/
    ├── staging/
    │   ├── kustomization.yaml
    │   ├── namespace.yaml
    │   ├── images.yaml
    │   ├── patches/
    │   └── README.md
    └── production/
        ├── kustomization.yaml
        ├── namespace.yaml
        ├── images.yaml
        ├── patches/
        └── README.md
```

## Kustomize Rules

- Base manifests define common workloads, services, service accounts, labels, probes, Redis, Traefik, cert-manager issuer templates, and SecretProvider/secret reference objects.
- Overlays define namespace, hostnames, image tags, resource profiles, replica counts, Secret Manager references, and environment labels.
- Overlays MUST NOT duplicate full workload manifests when a strategic merge or JSON patch is sufficient.
- Image tags MUST be set to the Git commit SHA for project images.
- `latest` MUST NOT be used for project image deployment.

## Required Labels

Every workload and service SHOULD include:

```yaml
app.kubernetes.io/name: helmet-violation-detection
app.kubernetes.io/component: <component-name>
app.kubernetes.io/part-of: helmet-violation-system
app.kubernetes.io/managed-by: kustomize
app.kubernetes.io/version: <commit-sha>
environment: <staging|production>
```

## Health Probe Expectations

- FastAPI services expose a health endpoint or equivalent readiness check.
- Frontend readiness verifies the Next.js server is accepting requests.
- Redis readiness uses Redis ping.
- Inference Worker readiness may use worker process health and queue connectivity rather than an HTTP endpoint.

## Exposure Rules

- Public routing is declared only through Traefik resources.
- Public routes must match the approved route contract.
- Internal services use ClusterIP.
- The Traefik Service is the only public LoadBalancer Service.

## TLS Rules

- Demo/production overlays must reference a DuckDNS host.
- cert-manager resources must request Let's Encrypt certificates.
- HTTP-01 solver traffic must be routable through the configured Traefik ingress class.
- Temporary LoadBalancer IP use is allowed only before demo readiness.

## Secret Rules

- Manifest files contain Secret Manager references only, never plaintext secret values.
- Kubernetes service accounts must be named consistently for IAM bindings.
- Environment overlays must be able to select distinct secret references.

## Validation Commands

Each overlay must pass:

```bash
kubectl kustomize deploy/k8s/overlays/staging
kubectl kustomize deploy/k8s/overlays/production
```

If `kustomize` is installed separately, the equivalent `kustomize build` commands are acceptable.
