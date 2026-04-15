# Project Status

## Current phase

Backend Phases 1-6 are complete. Frontend simulator scaffold is now in progress with a working production build.

## Completed

- Reviewed `plan.md` against the workbook in `reference/Calculadora_CCB.xlsx`.
- Corrected the spec around IOF gross-up, CET cash-flow construction, and the month-0 sample response.
- Created the backend package skeleton under `backend/`.
- Added YAML-backed pricing parameters in `backend/config/pricing_params.yaml`.
- Implemented:
  - settings loader
  - domain enums and input/output models
  - pricing engine with annual-to-monthly conversion
  - health endpoint scaffold
  - initial pricing parity tests
- Moved the workbook into `reference/` as a persistent parity artifact.
- Built a Python 3.13 virtualenv at `backend/.venv`.
- Installed backend runtime and dev dependencies.
- Verified Phase 1 with:
  - `./.venv/bin/pytest`
  - `./.venv/bin/ruff check .`
  - `./.venv/bin/mypy src`
- Implemented Phase 2 modules:
  - `backend/src/ccb/engine/iof.py`
  - `backend/src/ccb/engine/fees.py`
  - `backend/src/ccb/engine/schedule.py`
  - `backend/src/ccb/utils/dates.py`
- Added Phase 2 tests:
  - `backend/tests/test_iof.py`
  - `backend/tests/test_fees.py`
  - `backend/tests/test_schedule.py`
- Verified Phase 2 with:
  - `./.venv/bin/pytest` → 11 passed
  - `./.venv/bin/ruff check .` → passed
  - `./.venv/bin/mypy src` → passed
- Added `pyxirr` and implemented `backend/src/ccb/engine/cet.py`.
- Added `backend/tests/test_cet.py`.
- Verified Phase 3 with:
  - `./.venv/bin/pytest` → 14 passed
  - `./.venv/bin/ruff check .` → passed
  - `./.venv/bin/mypy src` → passed
- Implemented quote assembly in `backend/src/ccb/engine/quote.py`.
- Added public API route in `backend/src/ccb/api/public.py`.
- Wired FastAPI app routing and CORS in `backend/src/ccb/main.py`.
- Added API integration coverage in `backend/tests/test_api_public.py`.
- Verified Phase 4 with:
  - `./.venv/bin/pytest` → 19 passed
  - `./.venv/bin/ruff check .` → passed
  - `./.venv/bin/mypy src` → passed
- Added internal analytics stub in `backend/src/ccb/engine/analytics.py`.
- Added bearer-token-gated internal route in `backend/src/ccb/api/internal.py`.
- Extended response models with `AnalyticsResult` and `InternalAnalysisResult`.
- Added internal API integration coverage in `backend/tests/test_api_internal.py`.
- Verified Phase 5 with:
  - `./.venv/bin/pytest` → 22 passed
  - `./.venv/bin/ruff check .` → passed
  - `./.venv/bin/mypy src` → passed
- Added backend containerization in `backend/Dockerfile`.
- Added compose setup in `docker-compose.yml`.
- Added root project docs in `README.md`.
- Added GitHub Actions CI in `.github/workflows/ci.yml`.
- Added root `.gitignore` and backend `.dockerignore`.
- Verified post-packaging backend checks:
  - `./.venv/bin/pytest` → 22 passed
  - `./.venv/bin/ruff check .` → passed
  - `./.venv/bin/mypy src` → passed
- Added frontend scaffold under `frontend/`:
  - `package.json`, `vite.config.js`
  - `index.html`, `faq.html`
  - `src/style.css`, `src/main.js`, `src/simulator.js`, `src/api.js`, `src/format.js`
  - `public/favicon.svg`, `src/assets/logo.svg`
- Added frontend containerization in `frontend/Dockerfile`.
- Extended `docker-compose.yml` to run both backend and frontend.
- Verified frontend build with `npm run build`.

## Next recommended work

- Refine the frontend UX with live browser testing against the running backend.
- Add frontend FAQ/content polish and any missing accessibility pass.
- If needed, add a frontend smoke check to CI.

## Notes for future sessions

- The workbook is the tie-breaker whenever `plan.md` prose is ambiguous.
- The Excel default scenario is:
  - amount `45000`
  - tenor `24`
  - interest payment `bullet`
  - parcela frequency `monthly`
- IOF parity must use gross-up:
  - `amount_brl * ((1 / (1 - iof_total_pct)) - 1)`
- CET borrower cash flow is based on full disbursement at `t=0`; financed fees/IOF are carried in face value rather than withheld.
- No Python dependencies were preinstalled in the environment at session start.
- The plan's coupon-mode monthly-rate example appears to be wrong. Using the workbook's annual-rate logic and the same monthly compounding formula, `0.28661413324776336 p.a.` converts to `0.021223248586474904 p.m.`, not `0.021184702219797595`.
- The active interpreter for the project should be `backend/.venv/bin/python` (Python 3.13.9), not macOS system Python 3.9.
- Bullet maturity logic in the schedule should mirror workbook row `178`: final principal payment equals the entire post-accrual outstanding balance after any coupon sweep in that month.
- Current schedule semantics:
  - month 0 `cash_flow_to_borrower` is net disbursement from the borrower perspective
  - borrower payments in later rows are negative `cash_flow_to_borrower`
  - in bullet mode, the final `principal_payment` carries the full balloon after current-month accrual and any coupon sweep
- CET implementation details:
  - `borrower_cash_flows_from_schedule()` filters to non-zero borrower cash-flow rows
  - default workbook parity uses only two non-zero rows: `+45000` on `2026-03-31` and `-83216.449643...` on `2028-03-31`
  - workbook target is `0.35930122733116154 p.a.` and `0.025910896050664434 p.m.`
- Public API notes:
  - `POST /api/v1/simulate` is live
  - current JSON serialization returns `Decimal` fields as strings, which the tests now assert explicitly
  - the public quote uses quantized response values while CET/schedule computations still operate on unquantized internals
  - bullet maturity rows now expose `principal_payment` and `interest_payment` separately in a borrower-meaningful way while preserving workbook totals
- Internal API notes:
  - `POST /api/v1/internal/analyze` is live
  - auth is a simple `Authorization: Bearer <INTERNAL_API_TOKEN>` check against `settings.internal_api_token`
  - analytics are intentionally stubbed for now; `fidc_irr_pa` and `debtor_irr_pa` currently mirror quote CET, `moic` is derived from quantized quote totals, and the CDI+/IPCA+ placeholders are zero
- Packaging / delivery notes:
  - `backend/Dockerfile` builds and runs the FastAPI app with `uvicorn ccb.main:app`
  - `frontend/Dockerfile` runs the Vite dev server on port `5173`
  - `docker-compose.yml` now provisions both backend and frontend services
  - CI currently covers backend lint, type check, and tests only; no frontend CI step yet
