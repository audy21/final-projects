import json
import sqlite3

DB_PATH = "./data.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    vendor TEXT,
    invoice_number TEXT,
    invoice_date TEXT,
    due_date TEXT,
    currency TEXT,
    subtotal REAL,
    tax REAL,
    total REAL,
    line_items TEXT,
    field_confidence TEXT,
    raw_text TEXT,
    error TEXT,
    uploaded_at TEXT NOT NULL,
    approved_at TEXT
);
"""

def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _connect()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

def _row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    for key in ("line_items", "field_confidence"):
        if d.get(key):
            d[key] = json.loads(d[key])
    return d

def create_invoice(filename, file_type, uploaded_at):
    conn = _connect()
    cur = conn.execute(
        "INSERT INTO invoices (filename, file_type, uploaded_at) VALUES (?, ?, ?)",
        (filename, file_type, uploaded_at)
    )
    conn.commit()
    invoice_id = cur.lastrowid
    conn.close()
    return invoice_id

def get_invoice(invoice_id):
    conn = _connect()
    row = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)

def list_invoices():
    conn = _connect()
    rows = conn.execute("SELECT * FROM invoices ORDER BY id DESC").fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]

def update_fields(invoice_id, fields):
    allowed = ["vendor", "invoice_number", "invoice_date", "due_date", "currency", "subtotal", "tax", "total"]
    sets, values = [], []
    for key in allowed:
        if key in fields:
            sets.append(f"{key} = ?")
            values.append(fields[key])
    if "line_items" in fields:
        sets.append("line_items = ?")
        values.append(json.dumps(fields["line_items"]))
    if not sets:
        return
    values.append(invoice_id)
    conn = _connect()
    conn.execute(f"UPDATE invoices SET {', '.join(sets)} WHERE id = ?", values)
    conn.commit()
    conn.close()

def set_status(invoice_id, status, error=None):
    conn = _connect()
    conn.execute("UPDATE invoices SET status = ?, error = ? WHERE id = ?", (status, error, invoice_id))
    conn.commit()
    conn.close()

def recover_stale():
    conn = _connect()
    conn.execute(
        "UPDATE invoices SET status = 'failed', "
        "error = 'Extraction interrupted (server restarted mid-processing).' "
        "WHERE status IN ('queued', 'extracting')"
    )
    conn.commit()
    conn.close()

def get_approved():
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM invoices WHERE status = 'approved' ORDER BY invoice_date"
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]

def get_stats():
    conn = _connect()
    counts = {"queued": 0, "extracting": 0, "needs_review": 0, "approved": 0, "failed": 0}
    for row in conn.execute("SELECT status, COUNT(*) c FROM invoices GROUP BY status"):
        if row["status"] in counts:
            counts[row["status"]] = row["c"]

    approved = conn.execute(
        "SELECT vendor, invoice_date, total FROM invoices WHERE status = 'approved'"
    ).fetchall()
    conn.close()

    total_spend = sum(r["total"] or 0 for r in approved)

    by_vendor = {}
    for r in approved:
        name = r["vendor"] or "Unknown vendor"
        by_vendor[name] = by_vendor.get(name, 0) + (r["total"] or 0)
    by_vendor = sorted(
        [{"vendor": k, "total": v} for k, v in by_vendor.items()],
        key=lambda x: x["total"], reverse=True
    )[:8]

    by_month = {}
    for r in approved:
        if not r["invoice_date"]:
            continue
        month = r["invoice_date"][:7]
        by_month[month] = by_month.get(month, 0) + (r["total"] or 0)
    by_month = [{"month": k, "total": by_month[k]} for k in sorted(by_month)]

    return {
        "counts": counts,
        "total_spend": total_spend,
        "by_vendor": by_vendor,
        "by_month": by_month,
    }