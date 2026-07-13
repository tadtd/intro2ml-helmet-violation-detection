param(
    [Parameter(Mandatory = $true)][string]$ProjectId
)

$ErrorActionPreference = "Stop"
$secrets = @(
    "helmet-supabase-url",
    "helmet-supabase-anon-key",
    "helmet-supabase-service-role-key",
    "helmet-supabase-jwt-secret",
    "helmet-supabase-video-bucket",
    "helmet-supabase-storage-bucket",
    "helmet-duckdns-token",
    "helmet-jwt-secret"
)

foreach ($secret in $secrets) {
    $exists = & gcloud secrets describe $secret --project $ProjectId 2>$null
    if ($LASTEXITCODE -ne 0) {
        & gcloud secrets create $secret --project $ProjectId --replication-policy automatic
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create secret $secret"
        }
        Write-Host "Created secret placeholder: $secret"
    } else {
        Write-Host "Secret already exists: $secret"
    }
}

Write-Host "Add secret versions manually or through approved secure automation."
