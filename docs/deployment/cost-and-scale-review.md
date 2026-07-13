# Cost And Scale Review

The initial deployment favors predictable cost over automatic scale-out.

## Initial Rules

- GKE Autopilot only
- Fixed replicas
- One public LoadBalancer
- CPU-only inference worker
- In-cluster Redis
- No HPA
- No GPU resources

## Review Metrics

- CPU request and usage
- Memory request and usage
- Pod restart count
- Inference job processing duration
- Login latency
- Upload-to-results smoke-test success rate

Use `deploy/scripts/win/collect-smoke-metrics.ps1` after each smoke test.
