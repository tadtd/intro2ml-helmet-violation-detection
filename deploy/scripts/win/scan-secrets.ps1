param(
    [string[]]$Paths = @("deploy", ".github/workflows", "docs/deployment")
)

$ErrorActionPreference = "Stop"
$patterns = @(
    "SUPABASE_SERVICE_ROLE_KEY\s*[:=]\s*['""][^'""]+",
    "SUPABASE_JWT_SECRET\s*[:=]\s*['""][^'""]+",
    "DUCKDNS_TOKEN\s*[:=]\s*['""][^'""]+",
    "-----BEGIN PRIVATE KEY-----"
)

$files = foreach ($path in $Paths) {
    if (Test-Path $path) {
        Get-ChildItem $path -Recurse -File
    }
}

foreach ($file in $files) {
    if ($file.Name -eq "scan-secrets.ps1") {
        continue
    }
    $content = Get-Content -Raw $file.FullName
    foreach ($pattern in $patterns) {
        if ($content -match $pattern) {
            throw "Potential plaintext secret in $($file.FullName)"
        }
    }
}

Write-Host "Secret scan passed"
