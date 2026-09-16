import os
import pandas as pd
import random
import re
import requests
import time
import traceback
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_CANDIDATES = [
    model.strip()
    for model in os.getenv("GEMINI_MODELS", "gemini-3.7-flash,gemini-flash-latest,gemini-3.5-flash").split(",")
    if model.strip()
]
API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
LIST_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"
MAX_RETRIES_PER_MODEL = 3
BASE_BACKOFF_SECONDS = 1
MAX_JITTER_SECONDS = 0.5
REQUEST_TIMEOUT_SECONDS = 45
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
DEFAULT_RETRY_AFTER_SECONDS = 20
MODEL_DISCOVERY_TIMEOUT_SECONDS = 10


def get_model_url(model_name):
    return API_URL_TEMPLATE.format(model=model_name)


def get_retry_delay_seconds(attempt):
    backoff = BASE_BACKOFF_SECONDS * (2 ** attempt)
    jitter = random.uniform(0, MAX_JITTER_SECONDS)
    return backoff + jitter


def parse_retry_after_seconds(response):
    retry_after_raw = response.headers.get("Retry-After")
    if retry_after_raw is None:
        return None

    try:
        retry_after_seconds = int(retry_after_raw)
        return retry_after_seconds if retry_after_seconds > 0 else None
    except ValueError:
        return None


def normalize_model_name(model_name):
    return model_name.replace("models/", "", 1) if model_name.startswith("models/") else model_name


def get_available_generate_content_models(headers):
    try:
        response = requests.get(
            LIST_MODELS_URL,
            headers=headers,
            params={"key": API_KEY},
            timeout=MODEL_DISCOVERY_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            return None

        payload = response.json()
        available_models = set()
        for model_info in payload.get("models", []):
            methods = model_info.get("supportedGenerationMethods", [])
            if "generateContent" in methods:
                model_name = model_info.get("name")
                if isinstance(model_name, str):
                    available_models.add(normalize_model_name(model_name))
        return available_models
    except requests.RequestException:
        return None


def get_effective_model_candidates(headers):
    available_models = get_available_generate_content_models(headers)
    if not available_models:
        return MODEL_CANDIDATES

    filtered_models = [model for model in MODEL_CANDIDATES if normalize_model_name(model) in available_models]
    return filtered_models or MODEL_CANDIDATES


def extract_suggested_model_from_404(response):
    if response.status_code != 404:
        return None

    message = extract_upstream_error(response)
    match = re.search(r"models/([a-zA-Z0-9._-]+)", message)
    if not match:
        return None
    return normalize_model_name(match.group(1))


def call_model_with_retry_and_fallback(headers, payload):
    last_response = None
    last_model = None
    tried_models = []
    model_candidates = list(get_effective_model_candidates(headers))
    visited = set()
    index = 0

    while index < len(model_candidates):
        model_name = model_candidates[index]
        index += 1
        if model_name in visited:
            continue

        visited.add(model_name)
        tried_models.append(model_name)
        last_model = model_name
        model_url = get_model_url(model_name)

        for attempt in range(MAX_RETRIES_PER_MODEL):
            try:
                response = requests.post(
                    model_url,
                    headers=headers,
                    json=payload,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
            except requests.RequestException as exc:
                if attempt == MAX_RETRIES_PER_MODEL - 1:
                    break
                time.sleep(get_retry_delay_seconds(attempt))
                continue

            last_response = response
            if response.status_code == 200:
                return response, model_name, tried_models

            if response.status_code in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES_PER_MODEL - 1:
                time.sleep(get_retry_delay_seconds(attempt))
                continue

            suggested_model = extract_suggested_model_from_404(response)
            if suggested_model and suggested_model not in visited:
                model_candidates.append(suggested_model)
            break

    if last_response is None:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Failed to reach model provider after retries.",
                "model": last_model,
                "models_tried": tried_models,
            },
        )

    return last_response, last_model, tried_models


def extract_upstream_error(response):
    try:
        payload = response.json()
        error_payload = payload.get("error", {})
        if isinstance(error_payload, dict):
            message = error_payload.get("message")
            status = error_payload.get("status")
            if message and status:
                return f"{status}: {message}"
            if message:
                return message
        return str(payload)
    except ValueError:
        return response.text or "Unknown upstream error"


@app.post("/clean")
async def clean_data(file: UploadFile = File(...), instructions: str = Form("Clean this dataset.")):
    try:
        if not API_KEY:
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY is not set. Export your API key before starting the server.",
            )

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

        response, model_used, models_tried = call_model_with_retry_and_fallback(headers, payload)
        
        if response.status_code != 200:
            upstream_status = response.status_code if 400 <= response.status_code <= 599 else 502
            detail = {
                "message": extract_upstream_error(response),
                "model": model_used,
                "models_tried": models_tried,
            }
            if upstream_status in (429, 503):
                detail["retry_after_seconds"] = parse_retry_after_seconds(response) or DEFAULT_RETRY_AFTER_SECONDS
            raise HTTPException(status_code=upstream_status, detail=detail)

        data_json = response.json()
        
        if "candidates" not in data_json:
            raise HTTPException(status_code=500, detail=str(data_json))

        generated_text = data_json["candidates"][0]["content"]["parts"][0]["text"]
        clean_code = generated_text.replace("python", "").replace("```", "").strip()

        local_vars = {"df": df, "pd": pd}
        exec(clean_code, globals(), local_vars)
        
        return FileResponse(output_path, media_type="text/csv", filename="clean_data.csv")
    except HTTPException:
        raise
    except Exception as e:
        error_msg = traceback.format_exc()
        print(error_msg)
        raise HTTPException(status_code=500, detail=str(e))