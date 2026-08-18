# AI Data Cleaner

A FastAPI-based helper that asks a generative model to produce Python cleaning code for a provided CSV, executes that code locally, and returns a cleaned CSV.

Short summary
- This project is not a CLI tool. It runs as a web endpoint (/clean) that accepts a CSV upload and a short instructions string. The service sends a prompt (including a dataset preview) to an external generative API and expects valid Python code in the response. That code is executed against the uploaded dataframe to produce clean_data.csv, which is returned.

Important files
- app.py — FastAPI app; implements POST /clean
- dirty_data.csv — example input (if present)
- clean_data.csv — example output (produced by the service)
- temp_input.csv — temporary upload path used by the app

Dependencies (what the code imports)
- pandas
- fastapi
- requests
- uvicorn (recommended to serve the app)

Quick install
1. Create & activate virtualenv (adjust paths):
   python -m venv ../venv && source ../venv/bin/activate
2. Install dependencies:
   pip install pandas fastapi requests uvicorn

Run the app
- Start server: uvicorn app:app --reload --port 8000

Endpoint usage (example)
- cURL example (saves returned file as clean_data.csv):
  curl -X POST "http://localhost:8000/clean" \
    -F "file=@dirty_data.csv" \
    -F "instructions=Clean this dataset: coerce NA, parse dates, drop exact duplicates" \
    --output clean_data.csv

Screenshots
- ss1.png — initial state
- ss2.png — file and instructions filled
- ss3.png — processing
- ss4.png — final result

To show them in GitHub README, use relative image links like:

```md
![State awal](./screenshots/ss1.png)
![File + instructions](./screenshots/ss2.png)
![Processing](./screenshots/ss3.png)
![Hasil akhir](./screenshots/ss4.png)
```

Rendered preview:

![State awal](./screenshots/ss1.png)
![File + instructions](./screenshots/ss2.png)
![Processing](./screenshots/ss3.png)
![Hasil akhir](./screenshots/ss4.png)

What the endpoint does (implementation details)
- Saves uploaded file to temp_input.csv and reads it with pandas
- Builds a prompt containing a dataset preview and the provided instructions
- Calls an external Generative API (configured in app.py with URL and GEMINI_API_KEY)
- Expects the API response to contain valid Python code (no markdown)
- Strips code fences and executes the returned code with access to df and pd
- The executed code should write out clean_data.csv; the endpoint then returns that file

Security & notes (important)
- app.py reads GEMINI_API_KEY from the environment and calls exec() on model-generated code. Both are risky:
  - Keep API keys out of source control.
  - Executing untrusted code is unsafe. Only run this service with trusted models and in a controlled environment.

Accuracy of this README
- The previous README assumed a CLI with many flags (e.g. --fill-method, --drop-na). Those flags are NOT implemented in this repo. This README was updated to reflect the actual FastAPI behavior.

Suggested next steps (optional)
- Set GEMINI_API_KEY in your environment before running app.py
- Add a requirements.txt
- If you want a true CLI instead of the API, implement argument parsing and local cleaning logic (no model calls)

Contributing
- Open an issue or PR. Mention whether changes should keep the model-driven approach or switch to local deterministic cleaning steps.

If you want, update app.py to remove the hardcoded key or to add a CLI — say which and I can make a safe, minimal change.