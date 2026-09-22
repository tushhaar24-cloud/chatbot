# AI Assistant

Learning project built from [documents/BRD.md](documents/BRD.md).
React + TypeScript frontend, FastAPI backend, PostgreSQL, one LLM provider.

## Status

| Milestone | State |
|---|---|
| 1 — Project setup | done |
| 2 — Database (users, conversations, messages) | done |
| 3 — Authentication | done |
| 4 — Conversation APIs | next |
| 5 — Chat without AI (mock response) | |
| 6 — Integrate LLM | |

## Prerequisites

- Python 3.11 (`py -3.11`)
- Node 20+
- PostgreSQL 18 running on `localhost:5432` with database `chatbot_app`

## Running

Backend — port **8010** (8000–8003 are used by other apps on this machine):

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8010
```

Interactive API docs: http://localhost:8010/docs

## Schema management

No Alembic - the schema lives in `app/models/*.py` and is applied by
`backend/scripts/db.py`:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1

python -m scripts.db status        # compare models against the live database
python -m scripts.db create        # create missing tables (safe to re-run)
python -m scripts.db reset --yes   # drop everything and rebuild (DESTRUCTIVE)
python -m scripts.db sql "ALTER TABLE users ADD COLUMN name varchar(100)"
```

`create` only creates tables that do not exist. It cannot add a column to an
existing table - `status` reports that as DRIFT, and you fix it with either
`reset --yes` (destroys data) or a hand-written `sql` statement.

## Configuration

`backend/.env` holds database credentials and (from Milestone 6) the AI API key.
It is gitignored; `backend/.env.example` documents the shape.

`frontend/.env` holds only `VITE_API_BASE_URL`. Everything in it ships to the
browser, so no secret ever goes there.

## First-time setup

```powershell
# backend
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env    # then fill in POSTGRES_PASSWORD

# frontend
cd ..\frontend
npm install
```
