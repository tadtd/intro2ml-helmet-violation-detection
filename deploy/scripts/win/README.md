Run these scripts from the repository root in PowerShell.

Create empty Secret Manager entries:

```powershell
.\deploy\scripts\win\create-secret-manager-secrets.ps1 -ProjectId YOUR_PROJECT_ID
```

Push values from your local `.env` into GCP Secret Manager:

```powershell
.\deploy\scripts\win\push-secret-manager-values.ps1 -ProjectId YOUR_PROJECT_ID -EnvFile .env
```

Include DuckDNS only when your `.env` has `DUCKDNS_TOKEN` and you want it stored in Secret Manager:

```powershell
.\deploy\scripts\win\push-secret-manager-values.ps1 -ProjectId YOUR_PROJECT_ID -EnvFile .env -IncludeDuckDnsToken
```

The push script never prints secret values. It adds new Secret Manager versions for values it finds in `.env`.
