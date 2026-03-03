import requests

API_KEY = "rg_live_YOUR_KEY_HERE"
BASE_URL = "https://api.registrum.co.uk/v1"

res = requests.get(
    f"{BASE_URL}/company/00445790",
    headers={"X-API-Key": API_KEY},
)
print(res.json())
