param(
    [Parameter(Mandatory = $true)][string]$ProjectId,
    [string]$EnvFile = ".env",
    [switch]$CreateMissingSecrets,
    [switch]$IncludeDuckDnsToken,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    throw "gcloud was not found. Install Google Cloud CLI and run 'gcloud auth login' first."
}

if (-not (Test-Path -LiteralPath $EnvFile)) {
    throw "Env file not found: $EnvFile"
}

function Read-DotEnv {
    param([Parameter(Mandatory = $true)][string]$Path)

    $values = @{}

    foreach ($rawLine in Get-Content -LiteralPath $Path) {
        $line = $rawLine.Trim()

        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) {
            continue
        }

        if ($line.StartsWith("export ")) {
            $line = $line.Substring(7).Trim()
        }

        $separatorIndex = $line.IndexOf("=")
        if ($separatorIndex -lt 1) {
            continue
        }

        $key = $line.Substring(0, $separatorIndex).Trim()
        $value = $line.Substring($separatorIndex + 1).Trim()

        if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        if (-not [string]::IsNullOrWhiteSpace($key)) {
            $values[$key] = $value
        }
    }

    return $values
}

function Resolve-EnvValue {
    param(
        [Parameter(Mandatory = $true)]$Values,
        [Parameter(Mandatory = $true)][string[]]$Keys
    )

    foreach ($key in $Keys) {
        if ($Values.ContainsKey($key) -and -not [string]::IsNullOrWhiteSpace($Values[$key])) {
            return @{
                Key = $key
                Value = $Values[$key]
            }
        }
    }

    return $null
}

function Ensure-Secret {
    param([Parameter(Mandatory = $true)][string]$SecretName)

    & gcloud secrets describe $SecretName --project $ProjectId *> $null
    if ($LASTEXITCODE -eq 0) {
        return
    }

    if (-not $CreateMissingSecrets) {
        throw "Secret does not exist: $SecretName. Run create-secret-manager-secrets.ps1 first, or rerun with -CreateMissingSecrets."
    }

    if ($DryRun) {
        Write-Host "DRY RUN: would create secret $SecretName"
        return
    }

    & gcloud secrets create $SecretName --project $ProjectId --replication-policy automatic
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create secret $SecretName"
    }
}

function Add-SecretVersion {
    param(
        [Parameter(Mandatory = $true)][string]$SecretName,
        [Parameter(Mandatory = $true)][string]$Value
    )

    if ($DryRun) {
        Write-Host "DRY RUN: would add new version for $SecretName"
        return
    }

    $tempFile = [System.IO.Path]::GetTempFileName()
    try {
        Set-Content -LiteralPath $tempFile -Value $Value -NoNewline
        & gcloud secrets versions add $SecretName --project $ProjectId --data-file $tempFile *> $null
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to add secret version for $SecretName"
        }
    } finally {
        if (Test-Path -LiteralPath $tempFile) {
            Remove-Item -LiteralPath $tempFile -Force
        }
    }
}

$envValues = Read-DotEnv -Path $EnvFile

$secretMappings = @(
    @{ Secret = "helmet-supabase-url"; Keys = @("SUPABASE_URL") },
    @{ Secret = "helmet-supabase-anon-key"; Keys = @("SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY") },
    @{ Secret = "helmet-supabase-service-role-key"; Keys = @("SUPABASE_SERVICE_ROLE_KEY") },
    @{ Secret = "helmet-supabase-jwt-secret"; Keys = @("SUPABASE_JWT_SECRET") },
    @{ Secret = "helmet-supabase-video-bucket"; Keys = @("SUPABASE_VIDEO_BUCKET") },
    @{ Secret = "helmet-supabase-storage-bucket"; Keys = @("SUPABASE_STORAGE_BUCKET", "SUPABASE_VIOLATION_BUCKET") }
)

if ($IncludeDuckDnsToken) {
    $secretMappings += @{ Secret = "helmet-duckdns-token"; Keys = @("DUCKDNS_TOKEN") }
}

$missingValues = @()

foreach ($mapping in $secretMappings) {
    $resolved = Resolve-EnvValue -Values $envValues -Keys $mapping.Keys
    if ($null -eq $resolved) {
        $missingValues += "$($mapping.Secret) from one of: $($mapping.Keys -join ', ')"
        continue
    }

    Ensure-Secret -SecretName $mapping.Secret
    Add-SecretVersion -SecretName $mapping.Secret -Value $resolved.Value
    Write-Host "Added version for $($mapping.Secret) from $($resolved.Key)"
}

if ($missingValues.Count -gt 0) {
    Write-Warning "Skipped secrets with missing env values:"
    foreach ($missingValue in $missingValues) {
        Write-Warning "  $missingValue"
    }
}

Write-Host "Done. Secret values were not printed."
