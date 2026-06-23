import requests
import json

def test_api():
    url = "http://localhost:8000/api/v1/automation/fill"
    payload = {
        "document_id": "d827e3a3-b694-404c-a874-2d90c7b801e5",
        "target_url": "http://erpretails.s3-website.ap-south-1.amazonaws.com/admin/customer/form?type=create"
    }
    
    print(f"Sending POST to {url}...")
    try:
        response = requests.post(url, json=payload, timeout=90)
        print(f"Status Code: {response.status_code}")
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_api()
