# Public Endpoint

Early development smoke tests may use the temporary Traefik LoadBalancer IP. Demo-ready and production-ready use requires DuckDNS and Let's Encrypt TLS.

## Flow

1. Deploy Traefik as the only public `LoadBalancer`.
2. Read the external IP from the Traefik Service.
3. Point the DuckDNS subdomain to that IP.
4. Allow cert-manager HTTP-01 challenge traffic through Traefik.
5. Confirm the certificate is valid.
6. Use `https://<yourname>.duckdns.org` and `wss://<yourname>.duckdns.org` for user traffic.

## Approved Public Routes

- `/`
- `/api/v1/videos`
- `/api/v1/violations`
- `/ws/status`
- `/ws/camera`

All other services remain internal-only.
