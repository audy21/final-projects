import os
import pandas as pd
import requests
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()
API_KEY = os.getenv("GEMINI_API_KEY")
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"

@app.post("/clean")
async def clean_data(file: UploadFile = File(...), instructions: str = Form("Clean this dataset.")):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set")

    input_path = "temp_input.csv"
    output_path = "clean_data.csv"
    
    with open(input_path, "wb") as buffer:
        buffer.write(await file.read())
        
    df = pd.read_csv(input_path)
    data_preview = df.to_string()

    prompt = f"""
Dataset preview:
{data_preview}

Task:
{instructions}
Save the cleaned dataframe to clean_data.csv.
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
        raise HTTPException(status_code=500, detail=response.text)

    result = response.json()
    
    if "candidates" not in result:
        raise HTTPException(status_code=500, detail=str(result))

    generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
    clean_code = generated_text.replace("python", "").replace("```", "").strip()

    local_vars = {"df": df, "pd": pd}
    exec(clean_code, globals(), local_vars)
    
    return FileResponse(output_path, media_type="text/csv", filename="clean_data.csv")