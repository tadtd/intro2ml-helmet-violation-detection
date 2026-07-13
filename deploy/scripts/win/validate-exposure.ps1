param(
    [string]$Overlay = "staging",
    [string]$Root = "deploy/k8s/overlays"
)

$ErrorActionPreference = "Stop"
$manifest = & kubectl kustomize (Join-Path $Root $Overlay)
if ($LASTEXITCODE -ne 0) {
    throw "Unable to render overlay $Overlay"
}

$lbCount = ([regex]::Matches($manifest, "type:\s+LoadBalancer")).Count
if ($lbCount -ne 1) {
    throw "Expected exactly one LoadBalancer Service, found $lbCount"
}

$forbidden = @("auth-service", "orchestration-service", "inference-worker", "redis")
foreach ($name in $forbidden) {
    $routePattern = "kind:\s+IngressRoute[\s\S]*name:\s+$name"
    if ($manifest -match $routePattern) {
        throw "Forbidden internal service appears in public routing: $name"
    }
}

Write-Host "Exposure validation passed for $Overlay"
