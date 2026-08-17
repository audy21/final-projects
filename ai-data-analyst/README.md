# Analis Data

Query your database in Indonesian. Ask business questions in plain language, get SQL queries generated automatically, and see results with charts.

This is a full-stack demo project combining natural language processing, SQL generation, and data visualization. Built as a portfolio piece to show integration of multiple technologies.

## What It Does

You log in, ask a question like "How many successful transactions this week?" in Indonesian, and the system converts it to SQL, runs it, and shows you a table. If the data looks like a timeline or categories with numbers, it automatically draws a chart. You can download results as CSV or save charts as PNG.

The AI uses your actual database schema, so it knows what tables and columns exist. It tries to follow your phrasing—if you mention "rupiah amount" it knows to look at the `jumlah` column.

## Stack

- **Frontend**: HTML, CSS, vanilla JavaScript with Chart.js for visualization
- **Backend**: FastAPI running on Python, connects to SQLite or PostgreSQL
- **AI**: DeepSeek API for natural language to SQL conversion
- **Auth**: JWT tokens, bcrypt password hashing

Why DeepSeek? It's cheap, handles multilingual context well, and has enough token capacity for schema details. GPT-4 would work but costs more.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- A [DeepSeek API key](https://platform.deepseek.com) (free tier included)
- A browser that's not from 2010

### Setup

Clone or download this project, then:

```bash
cd backend
cp .env.example .env
```

Edit `.env` and paste your DeepSeek API key:

```
DEEPSEEK_API_KEY=sk-xxxxx...
JWT_SECRET=make-this-something-random-at-least-32-chars
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the backend:

```bash
uvicorn main.py:app --reload --host 0.0.0.0 --port 8004
```

You should see `Application startup complete`. Then open `index.html` in your browser (or use `python3 -m http.server 8000` and go to `http://localhost:8000`).

Log in with:
- Username: `admin`
- Password: `admin123`

## How to Test It

The demo includes sample data: 10 recent transactions, 10 employees across 4 departments, and 10 products.

Try these questions:

- "Berapa transaksi yang sukses minggu ini?" → Should return transactions with status 'sukses'
- "Karyawan divisi apa saja?" → Lists all departments
- "Produk apa yang stoknya menipis?" → Shows products with low stock
- "Jumlah transaksi per status" → Creates a bar chart by status

If a question doesn't work, the backend returns a user-friendly error. Check the browser console for details.

## The Database

SQLite by default with this schema:

```
transaksi       - date, amount (IDR), status
pengguna        - name, email, department
produk          - product name, price (IDR), stock
```

In the Settings tab, you can point it to a PostgreSQL database instead. It'll auto-detect the schema and run queries against that.

## How It Works Under the Hood

1. You submit a question in Indonesian
2. The backend fetches your database schema (table/column names)
3. It sends your question + schema to DeepSeek: "Convert this into a SELECT query"
4. DeepSeek returns SQL (without explanation, just the query)
5. Backend validates it's actually a SELECT, runs it against the database
6. Results come back as JSON: columns and rows
7. Frontend renders a table, checks if it should make a chart, shows your query

Validation happens at each step. If DeepSeek generates invalid SQL or something goes wrong, you see "Query failed or table not found. Try rewording."

## Structure

```
.
├── backend/
│   ├── main.py              - FastAPI app, database logic, AI integration
│   ├── requirements.txt      - Python dependencies
│   ├── .env.example          - Copy to .env and add your keys
│   └── data.db              - SQLite (created on first run)
├── index.html               - Login screen and main UI
├── script.js                - All frontend logic
├── styles.css               - Styling
└── README.md                - This file
```

## Development Notes

### Adding Your Own Database

Use the Settings tab to connect to PostgreSQL. The system will:
- Detect all public tables
- Extract column names and types
- Store the connection (in memory, not persisted)
- Use that database for all subsequent queries

To go back to SQLite, just clear the settings.

### Making It Production-Ready

Before deploying:

1. Change `JWT_SECRET` to something secure (32+ random characters)
2. Replace CORS `allow_origins=["*"]` with your actual domain
3. Remove the demo admin account or change its password
4. Use environment variables, never hardcode secrets
5. Add HTTPS (FastAPI can run behind nginx/apache)
6. Consider query timeouts—currently 5 seconds for database connections

### Limitations and Tradeoffs

- **No query caching**: Same question runs fresh each time
- **Single user**: Auth exists but all users share the same database connection
- **No audit logging**: Queries aren't tracked for compliance
- **LLM dependency**: If DeepSeek API is down, nothing works
- **No query approval**: Any query the AI generates runs immediately

These are fine for a demo. Production use would need additional safeguards.

## Testing

The backend includes a demo database. To verify everything works:

```bash
cd backend
python3 -m pytest  # (if you add tests)
```

Or manually:

```bash
# Terminal 1: Start backend
cd backend
uvicorn main.py:app --reload

# Terminal 2: Test the /health endpoint
curl http://localhost:8004/health
# Should return: {"status":"ok"}

# Test login
curl -X POST http://localhost:8004/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
# Should return a token

# Test a query (use token from above)
curl -X POST http://localhost:8004/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{"text":"Berapa transaksi sukses?"}'
```

Or just use the browser UI—it's faster.

## Potential Issues

**"Cannot connect to localhost:8004"**: Make sure the backend is running. Check that port 8004 isn't in use.

**"DeepSeek API error"**: Verify your API key in `.env`. Check that you have API credits.

**Database connection error**: If using PostgreSQL, verify host, port, and credentials. The 5-second timeout might be too short for slow networks.

**Blank table**: This is normal if the query returns no results. You'll see "No data for this question."

## What I Learned Building This

- **Schema-aware prompting works**: Telling the LLM your exact table structure massively improves SQL generation
- **Simple error handling beats detailed errors**: Users don't want stack traces, just "try rewording this"
- **Chart auto-detection is fragile**: Detecting if data is "dates + numbers" or "categories + numbers" requires heuristics. Future: let users pick chart type manually
- **Indonesian language generation is surprisingly good**: DeepSeek handles it better than I expected

## License

MIT. Use however you want.

