# Portfolio Tracker API

FastAPI + PostgreSQL (SQLAlchemy 2.0, async) REST API for tracking investment
portfolios: JWT auth, real-time price fetching (Yahoo Finance), and automated
P&L calculation using the weighted-average-cost method. Containerized with
Docker; deploys as-is to Render (or any Docker host).

## Run with Docker (recommended)

```
docker compose up --build
```

This starts Postgres, runs Alembic migrations, and serves the API on
http://localhost:8000. Interactive docs: http://localhost:8000/docs

## Run locally without Docker

Requires a running PostgreSQL instance.

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL / JWT_SECRET_KEY as needed
alembic upgrade head
uvicorn app.main:app --reload
```

## API overview

Auth (JWT bearer tokens):
- `POST /auth/register` — `{email, password}`
- `POST /auth/login` — form-encoded `username`/`password`, returns `{access_token}`
- `GET /auth/me`

Portfolios (all require `Authorization: Bearer <token>`):
- `POST /portfolios` — `{name}`
- `GET /portfolios`
- `GET /portfolios/{id}`
- `GET /portfolios/{id}/pnl` — per-holding realized/unrealized P&L + totals

Transactions:
- `POST /portfolios/{id}/transactions` — `{ticker, type: "buy"|"sell", quantity, price, fee, executed_at}`
- `GET /portfolios/{id}/transactions`

Prices:
- `GET /prices/{ticker}` — live price (Yahoo Finance, cached 60s)

## Design notes

- **Schema**: `users` → `portfolios` → `transactions` → `assets`, normalized
  so ticker/name data isn't duplicated per transaction. Holdings and cost
  basis are derived from the transaction ledger rather than stored
  redundantly.
- **P&L**: weighted-average-cost method — each sell realizes P&L against the
  running average cost of the position at that point; unrealized P&L compares
  the live price against the remaining position's average cost.
- **Prices**: `yfinance`, wrapped in a thread pool (it's a blocking library)
  with a short in-memory TTL cache to keep requests fast and avoid rate limits.
