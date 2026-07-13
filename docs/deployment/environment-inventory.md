# Environment Inventory

Values copied from `.env.example` must be supplied through environment-specific configuration or Secret Manager.

## Public Frontend Values

| Name | Source | Secret? | Notes |
|------|--------|---------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | Config/Secret Manager reference | No | Supabase project URL safe for browser use |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Secret Manager | No, but controlled | Browser-safe Supabase publishable key |
| `NEXT_PUBLIC_API_URL` | Kustomize overlay | No | HTTPS DuckDNS URL for API routes |
| `NEXT_PUBLIC_WS_URL` | Kustomize overlay | No | WSS DuckDNS URL for WebSocket routes |

## Backend Secret Values

| Name | Source | Secret? | Notes |
|------|--------|---------|-------|
| `SUPABASE_URL` | Secret Manager | Yes | Runtime Supabase project URL |
| `SUPABASE_ANON_KEY` | Secret Manager | Yes | Used for authorized Supabase access |
| `SUPABASE_SERVICE_ROLE_KEY` | Secret Manager | Yes | Server-only; never expose to frontend |
| `SUPABASE_JWT_SECRET` | Secret Manager | Yes | JWT verification |
| `DB_URL` | Secret Manager/manual admin only | Yes | CLI/admin use only |
| `DUCKDNS_TOKEN` | Secret Manager | Yes | DNS update automation if enabled |

## Runtime Non-Secret Values

| Name | Source | Notes |
|------|--------|-------|
| `ENVIRONMENT` | Overlay | `staging` or `production` |
| `REDIS_URL` | ConfigMap | `redis://redis:6379/0` in cluster |
| `SUPABASE_VIDEO_BUCKET` | ConfigMap | Defaults to `videos` |
| `SUPABASE_STORAGE_BUCKET` | ConfigMap | Defaults to `violations` |
| `USE_STUB_INFERENCE` | Overlay | `false` for real demo deployment |
