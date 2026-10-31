# NagarNexus Installation, Execution, Testing & Troubleshooting Guide

## 1. Local Execution on Windows PowerShell (Without Docker)

### Step A: Start the Backend Server

Open Windows PowerShell in the `NagarNexus` root directory:

```powershell
cd backend

# Create virtual environment (if not already created)
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements.txt

# Optional: Copy environment template
Copy-Item .env.example .env -ErrorAction SilentlyContinue

# Initialize database, sample datasets, and baseline ML models
python ..\scripts\initialize_database.py

# Start FastAPI server on http://localhost:8000
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Backend API Base URL: `http://localhost:8000/api`
- Interactive Swagger API Docs: `http://localhost:8000/docs`
- Default Demo Analyst Account: `analyst@nagarnexus.org` / `NagarNexus@2026`

### Step B: Start the Frontend Development Server

Open a second Windows PowerShell terminal in the `NagarNexus` root directory:

```powershell
cd frontend

# Install Node.js dependencies
npm install

# Start Vite development server on http://localhost:5173
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 2. Execution with Docker Compose (PostgreSQL + Backend + Frontend)

```powershell
docker compose up --build
```

This starts:
- `nagarnexus-postgres` (PostgreSQL 16 on port `5432`)
- `nagarnexus-backend` (FastAPI on port `8000`, connected to PostgreSQL)
- `nagarnexus-frontend` (React + Vite on port `5173`)

---

## 3. Running Automated Tests

### Backend Pytest Suite

```powershell
$env:PYTHONPATH="backend"
.\backend\.venv\Scripts\pytest.exe backend/tests/test_nagarnexus_api.py -v
```

### Frontend Vitest Suite

```powershell
cd frontend
npm test
```

---

## 4. Database Migrations (Alembic)

To apply schema migrations to PostgreSQL or SQLite:

```powershell
cd backend
.\.venv\Scripts\alembic.exe upgrade head
```

---

## 5. Troubleshooting Guide

- **Port 8000 or 5173 already in use**:
  Change `--port 8001` in `uvicorn` and update `VITE_API_BASE_URL=http://localhost:8001/api` in `frontend/.env`.
- **PostgreSQL connection refused during local development**:
  By default, `backend/app/core/config.py` uses `sqlite:///./nagarnexus.db` when `DATABASE_URL` is not overridden, allowing immediate local execution without requiring a running PostgreSQL server. Set `DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/nagarnexus_db` in `backend/.env` when connecting to PostgreSQL.
- **External API offline or rate-limited**:
  `fetch_open_meteo_weather` and `fetch_openaq_air_quality` automatically catch network timeouts and gracefully fall back to stored database observations while labeling the response as `offline_fallback`.

