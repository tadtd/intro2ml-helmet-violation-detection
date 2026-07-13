param(
    [Parameter(Mandatory = $true)][string]$ProjectId,
    [Parameter(Mandatory = $true)][string]$ProjectNumber,
    [Parameter(Mandatory = $true)][string]$GcpServiceAccount,
    [string[]]$Namespaces = @("helmet-staging", "helmet-production")
)

$ErrorActionPreference = "Stop"
$ksaNames = @("frontend", "auth", "ingestion", "dashboard", "notification", "orchestration", "inference-worker", "realtime-stream")

foreach ($namespace in $Namespaces) {
    foreach ($ksa in $ksaNames) {
        $member = "serviceAccount:${ProjectId}.svc.id.goog[$namespace/$ksa]"
        & gcloud iam service-accounts add-iam-policy-binding $GcpServiceAccount `
            --project $ProjectId `
            --role roles/iam.workloadIdentityUser `
            --member $member
        if ($LASTEXITCODE -ne 0) {
            throw "Failed Workload Identity binding for $namespace/$ksa"
        }
    }
}

& gcloud projects add-iam-policy-binding $ProjectId `
    --member "serviceAccount:$GcpServiceAccount" `
    --role roles/secretmanager.secretAccessor

Write-Host "Workload Identity bindings configured"
