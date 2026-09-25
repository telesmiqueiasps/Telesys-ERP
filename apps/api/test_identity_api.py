import sys
import requests

# Force UTF-8 stdout encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000/api/v1"


def test_api():
    print("--- 1. Testing Healthcheck Endpoint ---")
    res = requests.get(f"{BASE_URL}/health")
    print("Health response:", res.json())
    assert res.status_code == 200
    assert res.json()["database"] == "connected"
    print("✅ Healthcheck PASSED")

    print("\n--- 2. Testing Auth Login Endpoint ---")
    login_payload = {
        "email": "admin@telesys.com.br",
        "password": "admin123"
    }
    res = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    print("Login status code:", res.status_code)
    assert res.status_code == 200
    tokens = res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    print("✅ Login PASSED. Tokens acquired.")

    headers = {"Authorization": f"Bearer {access_token}"}

    print("\n--- 3. Testing GET /auth/me Endpoint ---")
    res = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print("Me response status:", res.status_code)
    assert res.status_code == 200
    user_data = res.json()
    print(f"User: {user_data['name']} ({user_data['email']})")
    print(f"Tenant: {user_data['tenant']['name']}")
    print(f"Companies count: {len(user_data['companies'])}")
    print(f"Permissions count: {len(user_data['permissions'])}")
    assert user_data["email"] == "admin@telesys.com.br"
    print("✅ /auth/me PASSED")

    print("\n--- 4. Testing POST /auth/refresh Endpoint ---")
    res = requests.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": refresh_token})
    print("Refresh status:", res.status_code)
    assert res.status_code == 200
    new_tokens = res.json()
    assert "access_token" in new_tokens
    print("✅ Token refresh PASSED")

    print("\n--- 5. Testing Protected Endpoints ---")
    res = requests.get(f"{BASE_URL}/tenants", headers=headers)
    assert res.status_code == 200
    print(f"Tenants count: {len(res.json())}")

    res = requests.get(f"{BASE_URL}/companies", headers=headers)
    assert res.status_code == 200
    print(f"Companies count: {len(res.json())}")

    res = requests.get(f"{BASE_URL}/roles/permissions", headers=headers)
    assert res.status_code == 200
    print(f"Permissions in system: {len(res.json())}")

    print("\n🎉 ALL ETAPA 2 IDENTITY & AUTH TESTS PASSED PERFECTLY!")


if __name__ == "__main__":
    test_api()
