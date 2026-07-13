param(
    [Parameter(Mandatory = $true)][string]$CommitSha,
    [ValidateSet("staging", "production")][string]$Environment = "staging",
    [string]$Namespace = "helmet-staging"
)

$ErrorActionPreference = "Stop"
$overlay = "deploy/k8s/overlays/$Environment"

kubectl apply -k $overlay
if ($LASTEXITCODE -ne 0) {
    throw "Apply failed for rollback overlay $overlay"
}

$deployments = @("frontend", "ingestion", "auth", "dashboard", "notification", "orchestration", "inference-worker", "realtime-stream", "traefik")
foreach ($deployment in $deployments) {
    kubectl -n $Namespace rollout status "deployment/$deployment" --timeout=180s
    if ($LASTEXITCODE -ne 0) {
        throw "Rollback rollout failed for $deployment"
    }
}

Write-Host "Rollback applied for $Environment to SHA $CommitSha"
