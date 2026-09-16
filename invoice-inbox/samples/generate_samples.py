import subprocess
import tempfile
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = Path(__file__).parent

INVOICES = [
    {"file": "invoice_01.pdf", "vendor": "PT Maju Jaya", "no": "INV-2026-071", "date": "5 Juli 2026",
     "due": "5 Agustus 2026", "items": [("Jasa konsultasi", 2, 5000000), ("Biaya administrasi", 1, 500000)],
     "tax_rate": 0.11},
    {"file": "invoice_02.pdf", "vendor": "CV Sinar Abadi", "no": "INV-2026-072", "date": "12 Juli 2026",
     "due": "12 Agustus 2026", "items": [("Pengadaan alat tulis kantor", 1, 3250000)],
     "tax_rate": 0.11},
    {"file": "invoice_03.pdf", "vendor": "PT Teknologi Nusantara", "no": "INV-2026-073", "date": "20 Juli 2026",
     "due": "20 Agustus 2026", "items": [("Lisensi software tahunan", 1, 24000000)],
     "tax_rate": 0.11},
    {"file": "invoice_04.pdf", "vendor": "Toko Komputer Sejahtera", "no": "INV-2026-074", "date": "3 Agustus 2026",
     "due": "3 September 2026", "items": [("Monitor 24 inch", 4, 1750000), ("Kabel HDMI", 4, 85000)],
     "tax_rate": 0.11},
    {"file": "invoice_05.pdf", "vendor": "PT Global Logistik", "no": "INV-2026-075", "date": "10 Agustus 2026",
     "due": "", "items": [("Pengiriman kargo Jakarta-Surabaya", 3, 4200000)],
     "tax_rate": 0.11},
    {"file": "invoice_06.pdf", "vendor": "CV Kreatif Digital", "no": "INV-2026-076", "date": "25 Agustus 2026",
     "due": "25 September 2026", "items": [("Desain identitas visual", 1, 8750000)],
     "tax_rate": 0.11},
    {"file": "invoice_09.pdf", "vendor": "PT Sumber Makmur", "no": "", "date": "12 September 2026",
     "due": "12 Oktober 2026", "items": [("Jasa perbaikan AC", 2, 950000)],
     "tax_rate": 0.11},
]

IMAGES = [
    {"file": "invoice_07.png", "vendor": "PT Cahaya Elektrik", "no": "INV-2026-077", "date": "2 September 2026",
     "due": "2 Oktober 2026", "items": [("Lampu LED panel", 24, 185000)], "tax_rate": 0.11},
    {"file": "invoice_08.png", "vendor": "UD Bangun Jaya", "no": "INV-2026-078", "date": "10 September 2026",
     "due": "10 Oktober 2026", "items": [("Semen 50kg", 40, 68000), ("Pasir (m3)", 6, 320000)], "tax_rate": 0.11},
]

def rupiah(n):
    return f"Rp {n:,.0f}".replace(",", ".")

def html(inv):
    rows = ""
    subtotal = 0
    for i, (desc, qty, price) in enumerate(inv["items"]):
        amount = qty * price
        subtotal += amount
        rows += f"<tr><td>{i+1}</td><td>{desc}</td><td>{qty}</td><td>{rupiah(price)}</td><td>{rupiah(amount)}</td></tr>"
    tax = round(subtotal * inv["tax_rate"])
    total = subtotal + tax
    due_row = f"<p>Jatuh tempo: {inv['due']}</p>" if inv["due"] else ""
    number_row = f"<p>No. Invoice: {inv['no']}</p>" if inv["no"] else ""
    return f"""<html><head><style>
    body {{ font-family: Helvetica, Arial; padding: 48px; color: #111; }}
    .head {{ border-bottom: 2px solid #111; padding-bottom: 16px; margin-bottom: 24px; }}
    h1 {{ margin: 0 0 8px; letter-spacing: 2px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
    th, td {{ border-bottom: 1px solid #ccc; padding: 8px 6px; text-align: left; font-size: 13px; }}
    th {{ background: #f1f1f1; }}
    .totals {{ margin-top: 20px; text-align: right; font-size: 14px; }}
    .totals .grand {{ font-weight: bold; font-size: 16px; }}
    </style></head><body>
    <div class="head">
      <h1>INVOICE</h1>
      <p><b>{inv['vendor']}</b></p>
      {number_row}
      <p>Tanggal: {inv['date']}</p>
      {due_row}
    </div>
    <table>
      <tr><th>#</th><th>Deskripsi</th><th>Qty</th><th>Harga</th><th>Jumlah</th></tr>
      {rows}
    </table>
    <div class="totals">
      <p>Subtotal: {rupiah(subtotal)}</p>
      <p>PPN 11%: {rupiah(tax)}</p>
      <p class="grand">Total: {rupiah(total)}</p>
    </div>
    </body></html>"""

def render(spec, as_pdf):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html(spec))
        html_path = f.name
    out_path = OUT / spec["file"]
    if as_pdf:
        subprocess.run([CHROME, "--headless", "--disable-gpu",
                        f"--print-to-pdf={out_path}", "--no-pdf-header-footer", html_path],
                       check=True, capture_output=True)
    else:
        subprocess.run([CHROME, "--headless", "--disable-gpu",
                        f"--screenshot={out_path}", "--window-size=800,1100", html_path],
                       check=True, capture_output=True)
    print("wrote", out_path.name)

for spec in INVOICES:
    render(spec, as_pdf=True)
for spec in IMAGES:
    render(spec, as_pdf=False)