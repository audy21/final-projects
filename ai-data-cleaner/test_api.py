import os

import requests

API_KEY = os.getenv("GEMINI_API_KEY")
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

headers = {
    "Content-Type": "application/json",
    "X-goog-api-key": API_KEY,
}

payload = {
    "contents": [
        {
            "parts": [
                {"text": "Halo, apakah API ini berfungsi?"}
            ]
        }
    ]
}

response = requests.post(URL, headers=headers, json=payload)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
