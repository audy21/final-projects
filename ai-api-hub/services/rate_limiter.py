from fastapi import HTTPException, Request
from collections import defaultdict
import time

window_seconds = 60
max_requests = 10

request_log = defaultdict(list)

def check_rate_limit(request: Request):
    key = request.headers.get("x-api-key", "anonymous")
    now = time.time()

    request_log[key] = [t for t in request_log[key] if now - t < window_seconds]

    if len(request_log[key]) >= max_requests:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again shortly.")

    request_log[key].append(now)
    return True