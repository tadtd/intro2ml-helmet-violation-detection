# Quickstart & Validation Guide

## Prerequisites
- `psql` client installed (via PostgreSQL: [https://www.postgresql.org/download/](https://www.postgresql.org/download/))
- Access credentials to the shared Supabase test project — xin từ team lead

## Setup (Chạy lần đầu)

1. Copy file `.env.example` thành `.env` và điền thông tin kết nối:
   ```bash
   cp .env.example .env
   # Mở .env và điền DB_URL thực vào
   ```

2. Đặt biến môi trường (chạy mỗi phiên terminal hoặc thêm vào `.env`):

   **Windows PowerShell:**
   ```powershell
   $env:DB_URL = "postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
   ```

   **Linux/macOS:**
   ```bash
   export DB_URL="postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
   ```

## Chạy test

### Test schema (kiểm tra cấu trúc bảng và check constraints):
```bash
psql $DB_URL -f supabase/tests/test_schema.sql
```
**Kết quả mong đợi**: 20 dòng `ok 1` đến `ok 20`, ROLLBACK ở cuối.

### Test RLS (kiểm tra phân quyền operator/admin):
```bash
psql $DB_URL -f supabase/tests/test_rls.sql
```
**Kết quả mong đợi**: 6 dòng `ok 1` đến `ok 6`, ROLLBACK ở cuối.

## Lưu ý quan trọng
- Cả 2 test file đều nằm trong transaction `BEGIN...ROLLBACK` nên **KHÔNG ghi dữ liệu thật vào DB** — an toàn khi chạy nhiều lần.
- Nếu thấy lỗi `pgtap extension not found`, vào Supabase Dashboard → Database → Extensions → bật `pgtap`.



## Frontend Supabase Boundary

The frontend uses Supabase only for authentication:

- Allowed: `supabase.auth.signInWithPassword()`, session refresh, and reading the current auth user/session.
- Not allowed: direct `supabase.from(...)` table queries from frontend code.
- Not allowed: direct `supabase.storage` reads/writes from frontend code.
- Not allowed: direct `supabase.channel(...)` database realtime subscriptions for domain data.

Frontend dashboard data, evidence crop access, exports, uploads, and realtime notifications must call backend REST/WebSocket APIs. The backend owns service-role access, storage writes, signed URL generation, and audit/RBAC enforcement.