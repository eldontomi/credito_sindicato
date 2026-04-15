# CCB Union Credit Portal

Backend-first implementation of the CCB union credit simulator described in [plan.md](./plan.md). The pricing and schedule logic is validated against the workbook in [reference/Calculadora_CCB.xlsx](./reference/Calculadora_CCB.xlsx).

## Current status

- Backend Phases 1-6 are complete.
- Frontend simulator scaffold is in place with Vite, plain HTML, shared CSS, and vanilla JS.
- Public API is live at `POST /api/v1/simulate`.
- Internal API stub is live at `POST /api/v1/internal/analyze`.

## Local setup

### Backend

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn ccb.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The site will be available at `http://127.0.0.1:5173`.

If the backend is running on a different host, set `VITE_API_BASE_URL`.

## Docker

Run the backend with Docker Compose:

```bash
docker compose up --build
```

This starts:

- backend at `http://127.0.0.1:8000`
- frontend at `http://127.0.0.1:5173`

The backend still exposes a healthcheck at `GET /healthz`.

## Validation

Run the backend checks from `backend/`:

```bash
./.venv/bin/pytest
./.venv/bin/ruff check .
./.venv/bin/mypy src
```

Run the frontend production build from `frontend/`:

```bash
npm run build
```

Deploy the built frontend to Cloudflare Workers from the repository root:

```bash
npm run deploy
```

The Worker entrypoint is [worker/index.js](./worker/index.js) and the static
asset directory is configured in [wrangler.jsonc](./wrangler.jsonc).

## Public API example

```bash
curl -X POST http://127.0.0.1:8000/api/v1/simulate \
  -H 'Content-Type: application/json' \
  -d '{
    "amount_brl": 45000,
    "tenor_months": 24,
    "interest_payment": "bullet",
    "parcela_frequency": "monthly",
    "state": "SP",
    "disbursement_date": "2026-03-31"
  }'
```

Expected key fields in the response:

- `"nominal_rate_pa": "0.296937"`
- `"cet_pa": "0.359301"`
- `"total_debt_brl": "49473.33"`
- `"total_paid_brl": "83216.45"`

## Internal API example

```bash
curl -X POST http://127.0.0.1:8000/api/v1/internal/analyze \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer local-dev-token' \
  -d '{
    "amount_brl": 45000,
    "tenor_months": 24,
    "interest_payment": "bullet",
    "parcela_frequency": "monthly",
    "disbursement_date": "2026-03-31"
  }'
```

## Configuration

Key environment variables:

- `PRICING_PARAMS_PATH`
- `INTERNAL_API_TOKEN`
- `CORS_ALLOWED_ORIGINS`
- `APP_ENV`
- `LOG_LEVEL`

Pricing constants live in [backend/config/pricing_params.yaml](./backend/config/pricing_params.yaml).
