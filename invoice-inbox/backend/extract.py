import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

load_dotenv(override=True)

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY", "sk-your-key-here"),
    base_url="https://api.deepseek.com/v1",
)

CRITICAL_FIELDS = ["vendor", "invoice_number", "invoice_date", "total"]
AUTO_APPROVE_THRESHOLD = 0.8

STRUCTURE_PROMPT = """You extract structured data from Indonesian invoices.

Return ONLY a JSON object with this exact shape:
{
  "vendor": {"value": "<string or null>", "confidence": <0.0-1.0>},
  "invoice_number": {"value": "<string or null>", "confidence": <0.0-1.0>},
  "invoice_date": {"value": "<YYYY-MM-DD or null>", "confidence": <0.0-1.0>},
  "due_date": {"value": "<YYYY-MM-DD or null>", "confidence": <0.0-1.0>},
  "currency": {"value": "<IDR|USD|other or null>", "confidence": <0.0-1.0>},
  "subtotal": {"value": <number or null>, "confidence": <0.0-1.0>},
  "tax": {"value": <number or null>, "confidence": <0.0-1.0>},
  "total": {"value": <number or null>, "confidence": <0.0-1.0>},
  "line_items": {"value": [{"description": "...", "qty": <number>, "unit_price": <number>, "amount": <number>}], "confidence": <0.0-1.0>}
}

Rules:
- Numbers: plain numbers without thousand separators or currency symbols. "Rp 12.500.000" becomes 12500000.
- Dates: normalize to YYYY-MM-DD. "10 Agustus 2026" becomes "2026-08-10".
- Missing or unreadable field: value null and confidence 0.0.
- Confidence is your own certainty that the value is correct, per field.
- No commentary. JSON only."""

def extract_text_pdf(path):
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def extract_text_image(path):
    import ollama
    response = ollama.chat(
        model="llava:7b",
        messages=[{
            "role": "user",
            "content": "Transcribe all text from this invoice image exactly as written, preserving line breaks. Do not add commentary.",
            "images": [path],
        }],
    )
    return response["message"]["content"]

def _strip_fences(text):
    return re.sub(r"^```(json)?\s*|\s*```$", "", text.strip()).strip()

def structure_invoice(text):
    for attempt in range(2):
        response = client.chat.completions.create(
            model="deepseek-chat",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": STRUCTURE_PROMPT},
                {"role": "user", "content": text[:12000]},
            ],
        )
        raw = _strip_fences(response.choices[0].message.content)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            continue
    return None

def _flatten(extracted):
    fields, confidences = {}, {}
    for key, item in extracted.items():
        fields[key] = item.get("value")
        confidences[key] = float(item.get("confidence", 0.0))
    return fields, confidences

def _should_auto_approve(confidences):
    return all(confidences.get(f, 0.0) >= AUTO_APPROVE_THRESHOLD for f in CRITICAL_FIELDS)

def process_invoice(invoice_id, path, file_type):
    import db
    try:
        db.set_status(invoice_id, "extracting")
        text = extract_text_pdf(path) if file_type == "pdf" else extract_text_image(path)
        if not text or not text.strip():
            db.set_status(invoice_id, "failed", "No readable text found in the file.")
            return

        extracted = structure_invoice(text)
        if extracted is None:
            db.set_status(invoice_id, "failed", "Failed to parse AI extraction output.")
            return

        fields, confidences = _flatten(extracted)
        conn = db._connect()
        conn.execute(
            """UPDATE invoices SET vendor=?, invoice_number=?, invoice_date=?, due_date=?,
               currency=?, subtotal=?, tax=?, total=?, line_items=?, field_confidence=?,
               raw_text=?, error=NULL WHERE id=?""",
            (
                fields.get("vendor"), fields.get("invoice_number"), fields.get("invoice_date"),
                fields.get("due_date"), fields.get("currency"), fields.get("subtotal"),
                fields.get("tax"), fields.get("total"),
                json.dumps(fields.get("line_items") or []),
                json.dumps(confidences),
                text, invoice_id,
            ),
        )
        conn.commit()
        conn.close()

        from datetime import datetime, timezone
        if _should_auto_approve(confidences):
            conn = db._connect()
            conn.execute(
                "UPDATE invoices SET status='approved', approved_at=? WHERE id=?",
                (datetime.now(timezone.utc).isoformat(timespec="seconds"), invoice_id),
            )
            conn.commit()
            conn.close()
        else:
            db.set_status(invoice_id, "needs_review")
    except Exception as exc:
        db.set_status(invoice_id, "failed", str(exc))