import http.client
import json
import os
from urllib.parse import urlparse

# Load credentials from .env file
def load_env():
    env = {}
    # Look in the parent directory first
    env_paths = [".env", "../.env"]
    for path in env_paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env[k.strip()] = v.strip()
            break
    return env

config = load_env()
supabase_url = config.get("SUPABASE_URL")
service_key = config.get("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not service_key:
    print("Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing from .env")
    exit(1)

host = urlparse(supabase_url).netloc

HEADERS = {
    "apikey": service_key,
    "Authorization": f"Bearer {service_key}",
    "Content-Type": "application/json",
}

users = [
    {
        "email": "operator@system.com",
        "password": "password123",
        "email_confirm": True,
        "user_metadata": {"full_name": "Nhân viên vận hành"},
        "role": "operator",
    },
    {
        "email": "admin@system.com",
        "password": "password123",
        "email_confirm": True,
        "user_metadata": {"full_name": "Quản trị viên"},
        "role": "admin",
    },
]


def request(method, path, body=None, headers=None):
    conn = http.client.HTTPSConnection(host)
    conn.request(
        method,
        path,
        body=json.dumps(body) if body is not None else None,
        headers={**HEADERS, **(headers or {})},
    )
    response = conn.getresponse()
    status = response.status
    data = response.read().decode()
    conn.close()
    return status, data


def existing_user_ids():
    """Map email -> id for users already present in Supabase Auth."""
    status, data = request("GET", "/auth/v1/admin/users")
    if status != 200:
        print(f"Error: could not list existing users: {status} {data}")
        exit(1)
    return {u["email"]: u["id"] for u in json.loads(data).get("users", [])}


def ensure_auth_user(user, existing):
    """Create the auth user, or reuse it if the email is already registered."""
    if user["email"] in existing:
        print(f"Auth user already exists: {user['email']}")
        return existing[user["email"]]

    payload = {k: user[k] for k in ("email", "password", "email_confirm", "user_metadata")}
    status, data = request("POST", "/auth/v1/admin/users", body=payload)
    if status not in (200, 201):
        print(f"Failed to create {user['email']}: Status {status}, Detail: {data}")
        return None

    print(f"Created auth user: {user['email']}")
    return json.loads(data)["id"]


def upsert_profile(user_id, user):
    """The profiles row is what carries the role; auth user creation does not create it."""
    payload = {
        "id": user_id,
        "role": user["role"],
        "display_name": user["user_metadata"]["full_name"],
    }
    status, data = request(
        "POST",
        "/rest/v1/profiles",
        body=payload,
        headers={"Prefer": "resolution=merge-duplicates"},
    )
    if status not in (200, 201, 204):
        print(f"Failed to upsert profile for {user['email']}: Status {status}, Detail: {data}")
        return False

    print(f"Profile ready: {user['email']} -> role={user['role']}")
    return True


existing = existing_user_ids()
failures = 0

for user in users:
    user_id = ensure_auth_user(user, existing)
    if user_id is None or not upsert_profile(user_id, user):
        failures += 1

if failures:
    print(f"\n{failures} user(s) failed to seed.")
    exit(1)

print("\nSeeding complete.")
