import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def verify_dispatch():
    print("Verifying dispatch...")
    
    # 1. Login
    print("Logging in...")
    try:
        resp = requests.post(f"{BASE_URL}/api/token", data={"username": "admin", "password": "password123"})
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            sys.exit(1)
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    # 2. Get Data
    vehicles = requests.get(f"{BASE_URL}/api/vehicles/", headers=headers).json()
    orders = requests.get(f"{BASE_URL}/api/orders/", headers=headers).json()
    depots = requests.get(f"{BASE_URL}/api/depots/", headers=headers).json()

    if not vehicles or not orders or not depots:
        print("Missing data for dispatch.")
        sys.exit(1)

    # 3. Create Dispatch Task
    payload = {
        "vehicle_ids": [v['id'] for v in vehicles[:5]],
        "order_ids": [o['id'] for o in orders[:20]],
        "depot_id": depots[0]['id']
    }
    
    print("Starting dispatch...")
    resp = requests.post(f"{BASE_URL}/api/dispatch/run", json=payload, headers=headers)
    if resp.status_code != 202:
        print(f"Dispatch start failed: {resp.text}")
        sys.exit(1)
    
    task_id = resp.json()["task_id"]
    print(f"Task ID: {task_id}")

    # 4. Poll Status
    print("Polling status...")
    max_retries = 30
    for i in range(max_retries):
        resp = requests.get(f"{BASE_URL}/api/dispatch/status/{task_id}", headers=headers)
        if resp.status_code != 200:
            print(f"Poll failed ({resp.status_code}): {resp.text}")
            sys.exit(1)
        
        data = resp.json()
        status = data.get("status")
        print(f"Poll {i+1}: {status}")
        
        if status == "Success":
            print("Dispatch successful!")
            print(f"Result: {data.get('result', 'No result data')}")
            return
        elif status == "Failed":
             print(f"Dispatch failed: {data.get('error')}")
             sys.exit(1)
        
        time.sleep(1)

    print("Timeout waiting for dispatch.")
    sys.exit(1)

if __name__ == "__main__":
    verify_dispatch()
