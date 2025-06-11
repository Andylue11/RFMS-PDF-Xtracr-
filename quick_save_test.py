import requests
import json
from dotenv import load_dotenv
import os

load_dotenv(".env-test")
BASE_URL = os.getenv("RFMS_BASE_URL")
STORE_CODE = os.getenv("RFMS_STORE_CODE")
API_KEY = os.getenv("RFMS_API_KEY")

# Get session token
response = requests.post(f"{BASE_URL}/v2/session/begin", auth=(STORE_CODE, API_KEY), headers={"Content-Type": "application/json"})
session_token = response.json().get("sessionToken")

# Try different save endpoints for order AZ002805
order_id = "AZ002805"
endpoints_to_try = [
    f"/v2/order/{order_id}/update",
    f"/v2/order/update", 
    f"/v2/order/commit",
    f"/v2/order/finalize",
    f"/v2/order/save"
]

for endpoint in endpoints_to_try:
    for method in ["PUT", "PATCH", "POST"]:
        try:
            if method == "PUT":
                resp = requests.put(f"{BASE_URL}{endpoint}", auth=(STORE_CODE, session_token), headers={"Content-Type": "application/json"}, data=json.dumps({"orderId": order_id}))
            elif method == "PATCH":
                resp = requests.patch(f"{BASE_URL}{endpoint}", auth=(STORE_CODE, session_token), headers={"Content-Type": "application/json"}, data=json.dumps({"orderId": order_id}))
            else:
                resp = requests.post(f"{BASE_URL}{endpoint}", auth=(STORE_CODE, session_token), headers={"Content-Type": "application/json"}, data=json.dumps({"orderId": order_id}))
            
            if resp.status_code not in [404, 405]:
                print(f"{method} {endpoint}: {resp.status_code} - {resp.text[:100]}")
        except:
            pass 