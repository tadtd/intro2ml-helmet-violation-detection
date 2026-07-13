param(
    [Parameter(Mandatory = $true)][string]$BillingAccountId
)

$ErrorActionPreference = "Stop"
$budgets = & gcloud billing budgets list --billing-account $BillingAccountId --format json
if ($LASTEXITCODE -ne 0) {
    throw "Unable to list billing budgets"
}

$text = $budgets | Out-String
foreach ($threshold in @("0.5", "0.9", "1")) {
    if ($text -notmatch $threshold) {
        throw "Could not confirm budget threshold $threshold"
    }
}

Write-Host "Budget alert thresholds found"
