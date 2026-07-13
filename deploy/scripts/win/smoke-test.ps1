param(
    [Parameter(Mandatory = $true)][string]$BaseUrl,
    [string]$Namespace = "helmet-staging"
)

$ErrorActionPreference = "Stop"
$https = $BaseUrl.TrimEnd("/")

$checks = @(
    @{ Name = "frontend"; Url = "$https/" },
    @{ Name = "ingestion"; Url = "$https/api/v1/videos" },
    @{ Name = "violations"; Url = "$https/api/v1/violations" }
)

foreach ($check in $checks) {
    try {
        $response = Invoke-WebRequest -Uri $check.Url -Method Head -TimeoutSec 15 -SkipHttpErrorCheck
        Write-Host "$($check.Name): HTTP $($response.StatusCode)"
    } catch {
        throw "Smoke check failed for $($check.Name) at $($check.Url): $_"
    }
}

kubectl -n $Namespace get pods
kubectl -n $Namespace get svc
Write-Host "Smoke checks completed for $BaseUrl"
