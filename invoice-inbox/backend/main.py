import csv
import io
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv(override=True)

import db
import extract

db.init_db()
db.recover_stale()

app = FastAPI(title="Invoice Inbox")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg"}

def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def saved_path(invoice_id: int, filename: str) -> Path:
    suffix = Path(filename).suffix.lower()
    return UPLOAD_DIR / f"{invoice_id}{suffix}"

def file_type_for(filename: str) -> str:
    return "pdf" if filename.lower().endswith(".pdf") else "image"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/invoices", status_code=201)
def upload_invoice(background: BackgroundTasks, file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail="Supported formats: PDF, PNG, JPG.")

    invoice_id = db.create_invoice(file.filename, file_type_for(file.filename), now_iso())
    dest = saved_path(invoice_id, file.filename)
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    background.add_task(extract.process_invoice, invoice_id, str(dest), file_type_for(file.filename))
    return {"id": invoice_id, "status": "queued"}

@app.get("/invoices")
def invoices():
    return {"invoices": db.list_invoices()}

@app.get("/invoices/{invoice_id}")
def invoice_detail(invoice_id: int):
    inv = db.get_invoice(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    return inv

@app.get("/invoices/{invoice_id}/file")
def invoice_file(invoice_id: int):
    inv = db.get_invoice(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    path = saved_path(invoice_id, inv["filename"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(path, filename=inv["filename"])

class FieldUpdate(BaseModel):
    vendor: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    due_date: str | None = None
    currency: str | None = None
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None
    line_items: list | None = None

@app.patch("/invoices/{invoice_id}")
def edit_invoice(invoice_id: int, update: FieldUpdate):
    if not db.get_invoice(invoice_id):
        raise HTTPException(status_code=404, detail="Invoice not found.")
    db.update_fields(invoice_id, update.model_dump(exclude_none=True))
    return {"status": "ok"}

@app.post("/invoices/{invoice_id}/approve")
def approve_invoice(invoice_id: int):
    inv = db.get_invoice(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    conn = db._connect()
    conn.execute(
        "UPDATE invoices SET status='approved', approved_at=? WHERE id=?",
        (now_iso(), invoice_id),
    )
    conn.commit()
    conn.close()
    return {"status": "approved"}

@app.post("/invoices/{invoice_id}/retry")
def retry_invoice(invoice_id: int, background: BackgroundTasks):
    inv = db.get_invoice(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    db.set_status(invoice_id, "queued", None)
    path = saved_path(invoice_id, inv["filename"])
    background.add_task(extract.process_invoice, invoice_id, str(path), inv["file_type"])
    return {"status": "queued"}

@app.get("/stats")
def stats():
    return db.get_stats()

@app.get("/export.csv")
def export_csv():
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "vendor", "invoice_number", "invoice_date", "due_date",
                     "currency", "subtotal", "tax", "total", "approved_at"])
    for inv in db.get_approved():
        writer.writerow([inv["id"], inv["vendor"], inv["invoice_number"], inv["invoice_date"],
                         inv["due_date"], inv["currency"], inv["subtotal"], inv["tax"],
                         inv["total"], inv["approved_at"]])
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=invoices.csv"},
    )