param(
    [string[]]$Overlays = @("staging", "production"),
    [string]$Root = "deploy/k8s/overlays"
)

$ErrorActionPreference = "Stop"

foreach ($overlay in $Overlays) {
    $path = Join-Path $Root $overlay
    if (-not (Test-Path $path)) {
        throw "Overlay not found: $path"
    }

    $rendered = & kubectl kustomize $path
    if ($LASTEXITCODE -ne 0) {
        throw "Kustomize render failed for $overlay"
    }

    if ($rendered -match "image:\s+\S+:latest") {
        throw "Mutable image tag 'latest' found in $overlay"
    }
    if ($rendered -match "HorizontalPodAutoscaler|autoscaling/") {
        throw "HPA resources are not allowed in the initial deployment"
    }
    if ($rendered -match "nvidia.com/gpu") {
        throw "GPU resources are not allowed in the initial deployment"
    }
    if ($rendered -match "kind:\s+Secret[\s\S]*stringData:") {
        throw "Plaintext Kubernetes Secret stringData found in $overlay"
    }

    Write-Host "Rendered $overlay successfully"
}
