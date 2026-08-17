import os
import re
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
import jwt
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

load_dotenv()

app = FastAPI(title="Analis Data")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY", "sk-your-key-here"),
    base_url="https://api.deepseek.com/v1"
)

JWT_SECRET = os.getenv("JWT_SECRET", "rahasia-dev-jangan-pakai-di-production")
TOKEN_HOURS = 12

DB_PATH = "./data.db"

active_db = None
current_schema = None


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    salt, digest = stored.split("$")
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return secrets.compare_digest(check, digest)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT
        );
        CREATE TABLE IF NOT EXISTS riwayat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            ts TEXT
        );
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY,
            tanggal TEXT,
            jumlah INTEGER,
            status TEXT
        );
        CREATE TABLE IF NOT EXISTS pengguna (
            id INTEGER PRIMARY KEY,
            nama TEXT,
            email TEXT,
            divisi TEXT
        );
        CREATE TABLE IF NOT EXISTS produk (
            id INTEGER PRIMARY KEY,
            nama_barang TEXT,
            harga INTEGER,
            stok INTEGER
        );
    """)

    admin_count = conn.execute("SELECT COUNT(*) FROM admin").fetchone()[0]
    if admin_count == 0:
        conn.execute(
            "INSERT INTO admin (username, password_hash) VALUES (?, ?)",
            ("admin", hash_password("admin123"))
        )

    transaksi_count = conn.execute("SELECT COUNT(*) FROM transaksi").fetchone()[0]
    if transaksi_count == 0:
        conn.executescript("""
            INSERT INTO transaksi (id, tanggal, jumlah, status) VALUES
            (1, '2026-08-13', 2450000, 'sukses'),
            (2, '2026-08-13', 180000, 'gagal'),
            (3, '2026-08-12', 3200000, 'sukses'),
            (4, '2026-08-12', 975000, 'sukses'),
            (5, '2026-08-12', 640000, 'tertunda'),
            (6, '2026-08-11', 2100000, 'sukses'),
            (7, '2026-08-11', 450000, 'gagal'),
            (8, '2026-08-10', 1250000, 'sukses'),
            (9, '2026-08-10', 890000, 'tertunda'),
            (10, '2026-08-09', 3100000, 'sukses');

            INSERT INTO pengguna (id, nama, email, divisi) VALUES
            (1, 'Budi Santoso', 'budi@perusahaan.co.id', 'Operasional'),
            (2, 'Sari Dewi', 'sari@perusahaan.co.id', 'Keuangan'),
            (3, 'Andi Wijaya', 'andi@perusahaan.co.id', 'Penjualan'),
            (4, 'Rina Marlina', 'rina@perusahaan.co.id', 'Operasional'),
            (5, 'Dimas Pratama', 'dimas@perusahaan.co.id', 'Logistik'),
            (6, 'Lina Kartika', 'lina@perusahaan.co.id', 'Keuangan'),
            (7, 'Yoga Saputra', 'yoga@perusahaan.co.id', 'Penjualan'),
            (8, 'Maya Anggraini', 'maya@perusahaan.co.id', 'Operasional'),
            (9, 'Fajar Hidayat', 'fajar@perusahaan.co.id', 'Logistik'),
            (10, 'Nia Rahmawati', 'nia@perusahaan.co.id', 'Keuangan');

            INSERT INTO produk (id, nama_barang, harga, stok) VALUES
            (1, 'Printer Thermal', 1850000, 42),
            (2, 'Kertas A4 (rim)', 55000, 320),
            (3, 'Barcode Scanner', 2400000, 15),
            (4, 'Label Stiker (roll)', 120000, 88),
            (5, 'Laptop Lenovo', 9999000, 7),
            (6, 'Mouse Wireless', 145000, 60),
            (7, 'Monitor 24 inch', 1750000, 23),
            (8, 'UPS 1200VA', 980000, 12),
            (9, 'Rak Gudang', 3200000, 9),
            (10, 'Tinta Printer', 135000, 110);
        """)
    conn.commit()
    conn.close()


def extract_schema_sqlite():
    conn = sqlite3.connect(DB_PATH)
    tables = [
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' AND name NOT IN ('admin', 'riwayat')"
        )
    ]
    schema = []
    for t in tables:
        cols = [
            {"name": r[1], "type": r[2]}
            for r in conn.execute(f"PRAGMA table_info({t})")
        ]
        schema.append({"table": t, "columns": cols})
    conn.close()
    return schema


def extract_schema_postgres(conn):
    cur = conn.cursor()
    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' ORDER BY table_name"
    )
    tables = [r[0] for r in cur.fetchall()]
    schema = []
    for t in tables:
        cur.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = %s ORDER BY ordinal_position",
            (t,)
        )
        cols = [{"name": r[0], "type": r[1]} for r in cur.fetchall()]
        schema.append({"table": t, "columns": cols})
    cur.close()
    return schema


def build_schema_prompt(schema):
    lines = [
        "You convert Indonesian business questions into SQL SELECT queries.",
        "",
        "Schema:"
    ]
    for t in schema:
        cols = ", ".join(f"{c['name']} {c['type']}" for c in t["columns"])
        lines.append(f"CREATE TABLE {t['table']} ({cols});")
    lines += [
        "",
        "Rules:",
        "- Return ONLY the SQL SELECT statement. No explanation, no markdown fences.",
        "- Use LIKE '%...%' for keyword searches on text columns.",
        "- Column 'jumlah' is an amount in rupiah, 'harga' is a unit price in rupiah."
    ]
    return "\n".join(lines)


def generate_sql(text: str):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": build_schema_prompt(current_schema)},
            {"role": "user", "content": text}
        ]
    )
    sql = response.choices[0].message.content.strip()
    sql = re.sub(r"^```(sql)?\s*|\s*```$", "", sql).strip()
    if not re.match(r"^SELECT", sql, re.IGNORECASE):
        return None
    return sql


def execute_query(sql):
    if active_db is None:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(sql)
            rows = cur.fetchall()
            columns = [d[0] for d in cur.description] if cur.description else []
            return columns, [list(r) for r in rows]
        finally:
            conn.close()
    else:
        import psycopg2
        conn = psycopg2.connect(
            host=active_db["host"],
            port=active_db["port"],
            dbname=active_db["dbname"],
            user=active_db["username"],
            password=active_db["password"],
            connect_timeout=5
        )
        try:
            cur = conn.cursor()
            cur.execute(sql)
            columns = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchall()
            cur.close()
            return columns, [list(r) for r in rows]
        finally:
            conn.close()


def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token tidak ada.")
    token = authorization[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload["sub"]
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid.")


class LoginRequest(BaseModel):
    username: str
    password: str


class QueryRequest(BaseModel):
    text: str


class DbConfig(BaseModel):
    host: str
    port: str
    dbname: str
    username: str
    password: str


@app.post("/login")
def login(request: LoginRequest):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT username, password_hash FROM admin WHERE username = ?",
        (request.username,)
    ).fetchone()
    conn.close()
    if not row or not verify_password(request.password, row[1]):
        raise HTTPException(status_code=401, detail="Username atau password salah.")
    token = jwt.encode(
        {
            "sub": request.username,
            "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS)
        },
        JWT_SECRET,
        algorithm="HS256"
    )
    return {"token": token, "username": request.username}


@app.post("/query")
def query(request: QueryRequest, user: str = Depends(get_current_user)):
    text = request.text.strip()
    if not text:
        return {"error": "Pertanyaan tidak boleh kosong."}

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO riwayat (text, ts) VALUES (?, ?)",
        (text, datetime.now().isoformat(timespec="seconds"))
    )
    conn.commit()
    conn.close()

    sql = generate_sql(text)
    if sql is None:
        return {"error": "Model tidak menghasilkan kueri yang valid. Coba gunakan kata lain."}

    try:
        columns, rows = execute_query(sql)
    except Exception as e:
        error_msg = "Kueri tidak valid atau tabel tidak ditemukan. Coba ubah pertanyaan."
        return {"error": error_msg}

    return {"sql": sql, "columns": columns, "rows": rows}


@app.get("/history")
def history(user: str = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT text, ts FROM riwayat ORDER BY id DESC LIMIT 10"
    ).fetchall()
    conn.close()
    return {"history": [{"text": r[0], "ts": r[1]} for r in rows]}


@app.post("/db/connect")
def db_connect(request: DbConfig, user: str = Depends(get_current_user)):
    global active_db, current_schema

    if not request.host.strip():
        active_db = None
        current_schema = extract_schema_sqlite()
        return {
            "status": "connected",
            "engine": "sqlite",
            "tables": [t["table"] for t in current_schema]
        }

    import psycopg2
    port = request.port.strip() or "5432"
    try:
        conn = psycopg2.connect(
            host=request.host.strip(),
            port=port,
            dbname=request.dbname.strip(),
            user=request.username.strip(),
            password=request.password,
            connect_timeout=5
        )
    except Exception as e:
        return {"status": "failed", "error": f"Koneksi gagal: {e}"}

    try:
        schema = extract_schema_postgres(conn)
    except Exception as e:
        conn.close()
        return {"status": "failed", "error": f"Ekstraksi skema gagal: {e}"}
    conn.close()

    active_db = {
        "host": request.host.strip(),
        "port": port,
        "dbname": request.dbname.strip(),
        "username": request.username.strip(),
        "password": request.password
    }
    current_schema = schema
    return {
        "status": "connected",
        "engine": "postgresql",
        "tables": [t["table"] for t in current_schema]
    }


@app.get("/db/current")
def db_current(user: str = Depends(get_current_user)):
    engine = "sqlite" if active_db is None else "postgresql"
    info = None
    if active_db is not None:
        info = {
            "host": active_db["host"],
            "port": active_db["port"],
            "dbname": active_db["dbname"],
            "username": active_db["username"]
        }
    return {
        "engine": engine,
        "connection": info,
        "schema": current_schema
    }


@app.get("/health")
def health():
    return {"status": "ok"}


init_db()
current_schema = extract_schema_sqlite()
