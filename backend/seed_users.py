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

parsed_url = urlparse(supabase_url)
host = parsed_url.netloc

users = [
    {
        "email": "operator@system.com",
        "password": "password123",
        "email_confirm": True,
        "user_metadata": {"full_name": "Nhân viên vận hành"}
    },
    {
        "email": "admin@system.com",
        "password": "password123",
        "email_confirm": True,
        "user_metadata": {"full_name": "Quản trị viên"}
    }
]

for user in users:
    conn = http.client.HTTPSConnection(host)
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json"
    }
    
    print(f"Creating user: {user['email']}...")
    conn.request("POST", "/auth/v1/admin/users", body=json.dumps(user), headers=headers)
    response = conn.getresponse()
    data = response.read().decode()
    
    if response.status in (200, 201):
        print(f"Successfully created user {user['email']}")
    else:
        print(f"Failed to create {user['email']}: Status {response.status}, Detail: {data}")
    conn.close()
