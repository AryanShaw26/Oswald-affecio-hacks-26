# TrustMatch AI

> **Connect with confidence, not uncertainty.**
> A safety-first dating platform powered by AI Trust Scoring.

---

## V1 Scope

V1 establishes the full-stack foundation: React frontend ↔ FastAPI backend ↔ PostgreSQL database. No auth or AI features yet — those come in V2+.

## Architecture

```
Browser (React + Vite + Tailwind)
        │
        │  Axios / HTTP
        ▼
FastAPI (:8000)
  ├── CORS middleware
  ├── /health endpoint
  ├── /dev/test-user (DB verification)
  └── SQLAlchemy ORM
        │
        ▼
PostgreSQL (Neon Cloud)
  └── users table
```

## Prerequisites

| Tool | Version |
|------|---------|
| Node.js | 18+ |
| npm | 9+ |
| Python | 3.12+ |
| Git | any |
| PostgreSQL | Neon cloud (or local) |

---

## Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env          # edit VITE_API_BASE_URL if needed
npm run dev
# → http://localhost:5173
```

## Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux / WSL:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Fill in DATABASE_URL, SECRET_KEY, OPENAI_API_KEY

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# → http://localhost:8000
# → Swagger UI: http://localhost:8000/docs
```

---

## Environment Variables

### Backend (`backend/.env`)
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (Neon format) |
| `SECRET_KEY` | Random 32+ char secret for signing |
| `OPENAI_API_KEY` | Your OpenAI key (backend only, V3+ use) |
| `FRONTEND_URL` | CORS origin — `http://localhost:5173` in dev |

### Frontend (`frontend/.env`)
| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | Backend URL — `http://localhost:8000` |

> ⚠️ **Never** put database credentials or secret keys in frontend `.env` variables.

---

## Database Setup

1. Create a PostgreSQL database (Neon recommended: https://neon.tech)
2. Copy the connection string into `backend/.env` as `DATABASE_URL`
3. Tables are auto-created on first backend startup via SQLAlchemy `create_all`

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Root / welcome |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |
| `POST` | `/dev/test-user` | V1 DB write verification |
| `GET` | `/dev/test-user/{id}` | V1 DB read verification |

### Health Check
```bash
curl http://localhost:8000/health
# {"status":"ok","service":"TrustMatch AI backend"}
```

### Test DB Write
```bash
curl -X POST http://localhost:8000/dev/test-user \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'
```

---

## V1 Acceptance Criteria

- [x] React/Vite app starts without errors
- [x] Tailwind styles render with brand color system
- [x] React Router navigation works (Home, Discover, Login, Register, 404)
- [x] Axios service layer configured
- [ ] FastAPI starts successfully (requires `.env` with `DATABASE_URL`)
- [ ] `GET /health` returns HTTP 200
- [ ] CORS allows `http://localhost:5173`
- [ ] Backend reads `DATABASE_URL` from `.env`
- [ ] SQLAlchemy connects to PostgreSQL
- [ ] `users` table created
- [ ] Test user insert + retrieve works
- [x] `.env` not tracked by Git
- [x] No secrets in frontend source

---

## Security Notes

- `.env` files are in `.gitignore` — never commit credentials
- The frontend uses only `VITE_API_BASE_URL` — no secrets
- `/dev/test-user` endpoints are **V1 only** — remove before production
- Rotate any API key that has ever been pasted into chat or committed to Git
- Use `backend/.env.example` as a safe template to share

---

## V1 → V2 Roadmap

| Version | Feature |
|---------|---------|
| **V1** | Foundation — this version ✅ |
| V2 | Authentication & User Profiles (JWT) |
| V3 | Trust Score AI Engine (OpenAI) |
| V4 | Conversation Safety Analysis |
| V5 | Privacy Guardian (PII detection) |
| V6 | Dashboard & Aggregated APIs |
