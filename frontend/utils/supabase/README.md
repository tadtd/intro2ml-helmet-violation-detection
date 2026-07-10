# Frontend Supabase Boundary

Frontend Supabase utilities are auth-only.

Allowed here:
- browser sign-in/sign-out/session calls via `supabase.auth`
- server or middleware session refresh via `supabase.auth.getUser()`

Not allowed here:
- direct `.from(...)` table queries
- direct `.storage` reads/writes
- direct `.channel(...)` database realtime subscriptions

Dashboard data, uploads, evidence crop URLs, exports, and live updates must go through the backend REST/WebSocket APIs so RBAC, service-role access, signed URLs, and audit behavior stay centralized.