import os
import pandas as pd
import requests

API_KEY = os.getenv("GEMINI_API_KEY")
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"

def main():
    if not API_KEY:
        raise RuntimeError("API key is missing")

    df = pd.read_csv("dirty_data.csv")
    data_preview = df.to_string()

    prompt = f"""
Dataset preview:
{data_preview}

Task:
Clean this dataset using pandas.
1. Drop duplicate rows.
2. Fill missing age values with the column mean.
3. Fill missing values in the name and occupation columns with the string 'Unknown'.
4. Save the cleaned dataframe to clean_data.csv.

Return only valid Python code. Do not include markdown formatting or explanations.
"""

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": API_KEY
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    response = requests.post(URL, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(response.status_code)
        print(response.text)
        return

    result = response.json()
    generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
    
    clean_code = generated_text.replace("python", "").replace("```", "").strip()

    local_vars = {"df": df, "pd": pd}
    exec(clean_code, globals(), local_vars)
    print("Data cleaning completed. Output saved to clean_data.csv")

if __name__ == "__main__":
    main()