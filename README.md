# Helmet Violation Detection

Monorepo for a helmet violation detection system using Next.js, FastAPI, Celery,
Redis, Supabase, and ONNX Runtime.

## Setup

1. Create a Supabase project, create `videos` and `violations` storage buckets,
   and run the modules in `backend/supabase/schema/` in order. Detailed setup
   steps are in [docs/supabase-setup.md](docs/supabase-setup.md).
2. Copy `.env.example` to `.env` and fill Supabase values locally. Do not commit
   real `.env` files, service role keys, tokens, certificates, kubeconfigs, or
   private keys.
3. Start Redis, API, and worker:

```powershell
docker compose up --build
```

4. Start the frontend:

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:3000`; the API runs at
`http://localhost:8000`.

## Local Smoke Test

After `docker compose up --build`, verify the local runtime before Kubernetes or
CI/CD work. Full PowerShell smoke-test steps are in
[docs/devops-smoke-test.md](docs/devops-smoke-test.md).

```powershell
docker compose ps
Invoke-RestMethod -Uri http://localhost:8000/health -Method Get
```

The Compose stack must show Redis, API, and worker services running. Any
infrastructure change must update these local run and smoke-test instructions
when the commands or expected checks change.

## Deployment Artifact Review

Production handoff artifacts are reviewable outlines, not a production rollout.
Review them after the local Docker Compose smoke test passes:

- [k8s/README.md](k8s/README.md) for GKE manifest handoff, secret placeholder
  creation, image placeholder replacement, and failure notes.
- [k8s/kustomization.yaml](k8s/kustomization.yaml) for the manifest grouping.
- [.github/workflows/deploy-gke.yml](.github/workflows/deploy-gke.yml) for the
  GKE deployment pipeline outline using Artifact Registry and workload identity.

The existing `.github/deploy.yml` file is empty/nonstandard and is not the
target workflow. Terraform, Helm, ArgoCD, and External Secrets are not required
for this feature.

## Security Rules

- Frontend code uses only `NEXT_PUBLIC_SUPABASE_URL` and
  `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.
- Backend API and worker services read Supabase service role credentials only
  from environment variables or a secret manager.
- Kubernetes and CI/CD files must use secret placeholders or secret-manager
  references with documented creation steps, not hardcoded secret values.

## Model Weights

Place exported ONNX files in `backend/app/weights/`:

- `yolo_best.onnx`
- `rtdetr_best.onnx`
- `fasterrcnn_best.onnx`

The wrapper classes are wired for ONNX Runtime, but final output parsing depends
on the exported model tensor shape and class mapping.
