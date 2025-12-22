import requests

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "integration_valid_user3@example.com"
PASSWORD = "Test@123"

def test_login_and_access():
    # Login
    resp = requests.post(f"{BASE_URL}/auth/login", data={"username": EMAIL, "password": PASSWORD})
    if resp.status_code != 200:
        print("Login failed:", resp.text)
        return
    
    token = resp.json()["access_token"]
    print("Login successful.")
    
    # Get Appointments
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/appointments/me", headers=headers)
    print(f"Get Appointments: {resp.status_code}, data: {resp.json()}")
    
    # Health
    resp = requests.get(f"{BASE_URL}/health")
    print(f"Health: {resp.json()}")

if __name__ == "__main__":
    test_login_and_access()
