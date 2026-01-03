
import requests
import json
import sys

# Login to get token first
def login(username, password):
    url = "http://localhost:8000/api/token"
    # Using form data as typically expected by OAuth2PasswordRequestForm
    data = {
        "username": username,
        "password": password
    }
    response = requests.post(url, data=data)
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        sys.exit(1)
    return response.json()["access_token"]

def check_tasks(token):
    url = "http://localhost:8000/api/tasks/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Fetch tasks failed: {response.text}")
        return

    tasks = response.json()
    print(f"Fetched {len(tasks)} tasks.")
    
    for task in tasks:
        print(f"\nTask ID: {task['id']}")
        print(f"  Title: {task.get('title')}")
        print(f"  Total Distance: {task.get('total_distance')}")
        
        stops = task.get('stops', [])
        print(f"  Stops Count: {len(stops)}")
        
        if stops:
            first_stop = stops[0]
            print(f"  First Stop Customer: {first_stop.get('customer')}")
            if first_stop.get('customer'):
                print(f"    Coords: ({first_stop['customer'].get('x')}, {first_stop['customer'].get('y')})")
        
        geometries = task.get('path_geometries')
        print(f"  Path Geometries Present: {bool(geometries)}")
        if geometries:
            print(f"  Path Geometries Length: {len(geometries)}")

if __name__ == "__main__":
    # Assuming default credentials or whatever user set. 
    # Based on seed data, maybe 'admin' / 'password' exists? 
    # Or I should check seed_data.py to know a valid user.
    # Looking at auth store usage in frontend, it seems to default to admin/password.
    try:
        token = login("admin", "password123")
        check_tasks(token)
    except Exception as e:
        print(e)
