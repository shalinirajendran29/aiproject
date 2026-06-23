import urllib.request
import socket

def test_dns():
    hostname = "erpretails.s3-website.ap-south-1.amazonaws.com"
    print(f"Resolving {hostname}...")
    try:
        ip = socket.gethostbyname(hostname)
        print(f"Success! IP is {ip}")
    except Exception as e:
        print(f"DNS Resolution failed: {e}")
        
    url = "http://erpretails.s3-website.ap-south-1.amazonaws.com/admin/customer/form?type=create"
    print(f"\nFetching {url}...")
    try:
        response = urllib.request.urlopen(url, timeout=10)
        print(f"HTTP Status: {response.status}")
    except Exception as e:
        print(f"HTTP Request failed: {e}")

if __name__ == "__main__":
    test_dns()
