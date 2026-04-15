# CCB Union Credit Portal — Build Plan

**Audience:** Coding agent (Claude Code, Cursor agent, or similar autonomous coder).
**Goal:** Build a production-ready credit simulator portal for Brazilian union members. Includes (a) a backend API + computation engine porting our internal Excel calculator, and (b) a public-facing frontend that consumes the API. The pricing logic is ported from `Calculadora_CCB.xlsx` — the byte-match test cases at the end of this document are the source of truth.

---

## 1. Project Overview

### 1.1 What we're building

A **portal** where union members can:
1. Simulate a personal credit (CCB — Cédula de Crédito Bancário) loan: enter desired amount, choose payment structure, see the rate, the monthly installment, the CET, and the full amortization schedule.
2. (Future) Apply for the loan, sign documents, and receive disbursement.

This document covers **both the backend API/computation engine and the frontend simulator UI**. Underwriting, KYC, e-signature, and disbursement layers are out of scope for this build but referenced in §15.

### 1.2 What the user-facing flow looks like

Reference layout: `https://recargapay.com.br/ferramentas/simulador-emprestimo-consignado`

The user sees a form with:
- **Loan amount** (slider or numeric input, in BRL)
- **Tenor** (number of months — discrete pills: 12 / 18 / 24 / 30 / 36)
- **Interest payment structure** (toggle: Coupon / Bullet)
- **Principal payment frequency** (toggle: Monthly / Quarterly / Semiannual / Annual)

On any input change, the backend returns:
- Effective monthly and annual interest rate
- CET (Custo Efetivo Total) — monthly and annual
- Total IOF
- Total fees
- Monthly installment (if applicable)
- Total amount paid over the life of the loan
- Full amortization schedule (per-month: date, principal, interest, balance)

---

## 2. Context & Background (read this before coding)

### 2.1 What a CCB is

A **CCB (Cédula de Crédito Bancário)** is a Brazilian credit instrument — essentially a private promissory note governed by Lei 10.931/2004. It is the legal vehicle through which our firm extends credit to union members. From the borrower's perspective it functions like a personal loan; from our perspective it's a securitizable receivable that gets warehoused and ultimately distributed via FIDC (Fundo de Investimento em Direitos Creditórios).

### 2.2 What CET is and why it matters (non-negotiable)

**CET (Custo Efetivo Total)** is the all-in effective annual cost to the borrower, computed via XIRR on the cash flows the borrower actually pays (including IOF, fees, and interest). It is **mandatory disclosure pre-contract** under Resolução CMN 4.881/2020. The simulator must always display CET, not just the nominal interest rate.

### 2.3 What IOF is

**IOF (Imposto sobre Operações Financeiras)** is a federal tax on credit operations. For personal credit it is roughly:
- 0.38% fixed
- 0.0082% per day, capped at 365 days (~3% maximum)
- **Total cap: ~3.373% of principal**

The Excel model uses a flat **3.373%** as a simplifying assumption (the cap), but the workbook does **not** compute IOF as `principal * 3.373%`. It **grosses up** the requested amount so the borrower still receives the requested principal while IOF is financed into the CCB face value:

```python
iof_brl = amount_brl * ((1 / (1 - iof_total_pct)) - 1)
```

For v1, match the workbook exactly. Flag in code as a TODO to implement the statutory day-by-day formula in v2.

### 2.4 Monetary units

The Excel uses **R$ thousands** internally (`D20 = 45` means R$ 45,000). The API must accept and return values in **R$ (BRL units, not thousands)** — convert at the boundary.

---

## 3. Architecture Decisions

### 3.1 Two engines, one codebase

The Excel workbook actually contains two distinct engines glued together. Separate them cleanly:

| Module | Purpose | Exposed to |
|---|---|---|
| `pricing` | Resolves the debtor's nominal rate from inputs (base + 3 dimensional adjustments) | Public + Internal |
| `schedule` | Generates per-month cash flow: interest accrual, interest payment, principal amortization | Public + Internal |
| `cet` | XIRR of the borrower's cash flow including all fees, taxes, and payments | Public + Internal |
| `analytics` | FIDC IRR / Debtor IRR / MOIC / Duration / CDI+ / IPCA+ returns — for Prisma's investment review | **Internal only** |
| `macro` | Persisted CDI / IPCA / Selic curves, refreshed nightly from BCB SGS API | Internal |
| `reference` | RTD registry costs by state & amount, fees catalog | Both |

**Critical:** The public simulator must NOT expose the analytics layer. It contains internal pricing and return data that should never be visible to a borrower.

### 3.2 Stateless pricing core

The pricing/schedule/CET engines are **pure functions** with no I/O. Given a fully-populated `LoanInputs` object, they return a fully-populated `LoanQuote`. This makes them trivially testable and cacheable.

### 3.3 Configuration over hardcoding

Every numeric constant from the spreadsheet (base rate, ceiling rate, dimensional weights, fee percentages, IOF rate, escrow monthly fee) lives in a single `config.py` / `pricing_params.yaml`. **Do not embed any rates in Python code.** A non-developer (Tomás or another partner) must be able to update rates by editing YAML and restarting the service.

---

## 4. Tech Stack

### 4.1 Backend

| Layer | Choice | Rationale |
|---|---|---|
| Language | **Python 3.11+** | Financial logic is clearer in Python; rich numerical ecosystem |
| Web framework | **FastAPI** | Auto-generated OpenAPI docs, Pydantic validation, async support |
| Validation | **Pydantic v2** | Type-safe request/response models |
| IRR / XIRR | **`pyxirr`** (or `scipy.optimize.brentq` fallback) | `pyxirr` is ~100× faster than scipy, matches Excel's XIRR exactly |
| Date math | **`python-dateutil`** (specifically `relativedelta`) for end-of-month arithmetic | Excel's `EOMONTH` equivalent |
| Testing | **pytest** + **pytest-cov** | Standard |
| Config | **`pydantic-settings`** + YAML file | Hot-reloadable, env-overridable |
| Linting | **`ruff`** + **`mypy --strict`** | |
| Container | **Docker**, single-stage Python slim image | |
| API docs | Auto-generated Swagger at `/docs` | Standard FastAPI |

**Do not** use Django, Flask, or pandas. Pandas is overkill for this and adds 100MB to the container.

### 4.2 Frontend

The frontend mirrors an existing internal project's stack (proven dev experience, kept intentionally minimal):

| Layer | Choice |
|---|---|
| Build tool | **Vite `^8.0.0`** |
| Language | **Plain HTML + CSS + vanilla JavaScript** |
| Module system | **ES modules** (`"type": "module"` in `package.json`) |
| Styling | **One shared global stylesheet** at `src/style.css`, using CSS custom properties for tokens |
| Fonts | **Google Fonts** — extract from BT Créditos (see §14a) |
| Architecture | **Multi-page static site** — not a SPA, no router |
| State | **None** — DOM-driven with vanilla JS |
| HTTP | **`fetch()`** — no axios, no SWR, no TanStack Query |
| Dependencies | **Vite only** — zero UI libraries, zero state libraries |

**Do not** use React, Vue, Svelte, Next.js, Tailwind, Bootstrap, or any UI/state/routing library. The dev experience we want is plain HTML pages with shared CSS and small DOM-driven scripts. If you find yourself reaching for a framework, stop and reconsider.

---

## 5. Project Structure

Monorepo with two top-level folders, `backend/` and `frontend/`. Each is independently buildable, dockerizable, and deployable.

```
ccb-portal/
├── README.md                      # how to run both apps locally
├── docker-compose.yml             # spins up backend (and frontend dev server)
├── backend/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── .env.example
│   ├── config/
│   │   └── pricing_params.yaml    # all rates, fees, dimensional weights
│   ├── src/
│   │   └── ccb/
│   │       ├── __init__.py
│   │       ├── main.py            # FastAPI app entrypoint
│   │       ├── settings.py        # pydantic-settings; loads YAML
│   │       ├── api/
│   │       │   ├── __init__.py
│   │       │   ├── public.py      # POST /api/simulate
│   │       │   ├── internal.py    # POST /api/internal/analyze (auth-gated)
│   │       │   └── health.py
│   │       ├── domain/
│   │       │   ├── __init__.py
│   │       │   ├── inputs.py      # LoanInputs, enums
│   │       │   ├── outputs.py     # LoanQuote, ScheduleRow, AnalyticsResult
│   │       │   └── enums.py       # InterestPayment, ParcelaFrequency
│   │       ├── engine/
│   │       │   ├── __init__.py
│   │       │   ├── pricing.py     # rate determination
│   │       │   ├── schedule.py    # cash-flow generation
│   │       │   ├── cet.py         # XIRR-based CET calc
│   │       │   ├── iof.py         # IOF computation
│   │       │   ├── fees.py        # Fee catalog application
│   │       │   └── analytics.py   # Internal-only: FIDC IRR, MOIC, duration
│   │       ├── reference/
│   │       │   ├── __init__.py
│   │       │   ├── rtd.py         # State-dependent RTD lookup
│   │       │   └── macro.py       # CDI/IPCA/Selic series (stub for v1)
│   │       └── utils/
│   │           ├── __init__.py
│   │           └── dates.py       # EOMONTH equivalent
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_pricing.py        # byte-match test cases from §11
│   │   ├── test_schedule.py
│   │   ├── test_cet.py
│   │   ├── test_iof.py
│   │   ├── test_api_public.py     # FastAPI TestClient integration
│   │   └── fixtures/
│   │       └── golden_outputs.json
│   └── scripts/
│       └── verify_excel_parity.py
└── frontend/
    ├── package.json               # only dep: vite ^8
    ├── vite.config.js
    ├── index.html                 # the simulator page
    ├── faq.html                   # placeholder for future pages
    ├── public/                    # static assets served as-is
    │   └── favicon.svg
    └── src/
        ├── main.js                # shared front-end logic
        ├── style.css              # single global stylesheet (CSS custom props)
        ├── api.js                 # fetch wrapper for backend
        ├── simulator.js           # simulator page logic
        ├── format.js              # Intl.NumberFormat helpers (pt-BR)
        └── assets/
            ├── logo.svg
            └── icons/
```

The shapes of `frontend/src/main.js` and `frontend/src/style.css` mirror an existing internal project — see `stack.md` reference. Do not introduce a build-time component framework.

---

## 6. Domain Model & Schemas

### 6.1 Enums

```python
# src/ccb/domain/enums.py
from enum import Enum

class InterestPayment(str, Enum):
    COUPON = "coupon"      # Excel "Coupon" — pay interest periodically
    BULLET = "bullet"      # Excel "Bullet" — accrue interest, pay all at maturity

class ParcelaFrequency(str, Enum):
    MONTHLY     = "monthly"     # Excel "Mensal"      — switch value 1
    QUARTERLY   = "quarterly"   # Excel "Trimestral"  — switch value 2
    SEMIANNUAL  = "semiannual"  # Excel "Semestral"   — switch value 3
    ANNUAL      = "annual"      # Excel "Anual"       — switch value 4

class State(str, Enum):
    SP = "SP"
    RJ = "RJ"
    # extend as needed
```

### 6.2 Inputs

```python
# src/ccb/domain/inputs.py
from decimal import Decimal
from pydantic import BaseModel, Field
from .enums import InterestPayment, ParcelaFrequency, State

class LoanInputs(BaseModel):
    amount_brl: Decimal = Field(..., gt=0, le=Decimal("1000000"),
        description="Loan principal in BRL (not thousands).")
    tenor_months: int = Field(..., description="Loan term in months.")
    interest_payment: InterestPayment
    parcela_frequency: ParcelaFrequency
    state: State = State.SP  # affects RTD costs
    disbursement_date: date | None = None  # defaults to today

    @field_validator("tenor_months")
    @classmethod
    def _allowed_tenor(cls, v: int) -> int:
        if v not in (12, 18, 24, 30, 36):
            raise ValueError("tenor_months must be one of: 12, 18, 24, 30, 36")
        return v
```

**Note on tenor:** The Excel only supports these 5 discrete values because they map to switch positions in the rate formula (see §7). The frontend must restrict to these. If we later want continuous tenors, the rate formula needs reworking — flag this as a known limitation.

### 6.3 Outputs

```python
# src/ccb/domain/outputs.py
from decimal import Decimal
from datetime import date
from pydantic import BaseModel

class ScheduleRow(BaseModel):
    month: int                          # 0 = disbursement, 1..N = installments
    date: date
    interest_accrual: Decimal           # interest accrued this month
    interest_payment: Decimal           # interest actually paid this month
    principal_payment: Decimal          # principal amortization this month
    balance_eop: Decimal                # outstanding balance end-of-period
    cash_flow_to_borrower: Decimal      # negative when borrower pays

class LoanQuote(BaseModel):
    # Pricing
    nominal_rate_pa: Decimal            # debtor APR (e.g., 0.2969)
    nominal_rate_pm: Decimal            # debtor monthly rate (e.g., 0.02190)

    # Cost to borrower (CET = XIRR including all fees/taxes)
    cet_pa: Decimal
    cet_pm: Decimal

    # Money breakdown (in BRL, not thousands)
    principal_brl: Decimal              # = amount requested
    iof_brl: Decimal
    fees_brl: Decimal                   # sum of lawyer + BT + bank issuance + RTD
    total_debt_brl: Decimal             # principal + IOF + fees (CCB face value)
    total_paid_brl: Decimal             # sum of all borrower outflows over life
    total_interest_brl: Decimal         # total_paid - principal

    # Schedule
    schedule: list[ScheduleRow]

    # Echo of inputs for client convenience
    inputs: LoanInputs
```

---

## 7. The Pricing Engine (port from Excel)

This is the most critical section. Get this wrong and everything downstream is wrong.

### 7.1 Constants (load from `pricing_params.yaml`)

```yaml
# config/pricing_params.yaml
rates:
  base_pa: 0.267                       # Excel I37 — base annual rate (26.7%)
  ceiling_pa: 0.3358215201675907       # Excel I38 — ceiling annual rate (33.58%)
  weights:                             # how the spread (ceiling - base) is sliced
    payment_dim: 0.60                  # Excel I40: 60% of spread
    parcela_dim: 0.30                  # Excel I43: 30% of spread
    tenor_dim:   0.10                  # Excel I46: 10% of spread

# Switch tables — MUST match Excel exactly
switches:
  interest_payment:
    coupon: 1
    bullet: 2
  parcela_frequency:
    monthly:    1
    quarterly:  2
    semiannual: 3
    annual:     4
  tenor_months:
    12: 1
    18: 2
    24: 3
    30: 4
    36: 5

# Divisors for the linear scaling per dimension (Excel uses /4, /4, /5)
scaling_divisors:
  payment_dim: 4   # H30 divisor — 2 options × buffer
  parcela_dim: 4   # H31 divisor — 4 options
  tenor_dim:   5   # H32 divisor — 5 tenor buckets

fees:
  lawyer_origination_pct: 0.03         # D31 — 3%
  bt_closing_pct:         0.03         # D32 — 3%
  bank_issuance_pct_flat: 0.0045       # D34 — 0.45% flat
  bank_issuance_min_brl:  0            # D35 — minimum (currently 0)
  escrow_opening_brl:     0            # D38 — currently 0
  escrow_monthly_brl:     68           # D42 — R$ 68/month
  rtd_register_brl:       0            # D39 — currently disabled (was XLOOKUP)

taxes:
  iof_total_pct: 0.03373               # D45 — 3.373% (cap-based simplification)
```

### 7.2 Rate determination — exact formula port

```python
# src/ccb/engine/pricing.py
from decimal import Decimal
from ..domain.inputs import LoanInputs
from ..settings import settings

def compute_nominal_rate_pa(inputs: LoanInputs) -> Decimal:
    """
    Port of Excel cells I37 + I41 + I44 + I47.

    Formula (in Excel terms):
        I40 = (I38 - I37) * 60%          # payment-dim spread
        I41 = H30 / 4 * I40              # apply payment switch
        I43 = (I38 - I37) * 30%          # parcela-dim spread
        I44 = H31 / 4 * I43              # apply parcela switch
        I46 = (I38 - I37) * 10%          # tenor-dim spread
        I47 = H32 / 5 * I46              # apply tenor switch
        I49 = I37 + I41 + I44 + I47

    Where H30, H31, H32 are switch values (see config switches).
    """
    p = settings.pricing_params

    base    = Decimal(str(p.rates.base_pa))
    ceiling = Decimal(str(p.rates.ceiling_pa))
    spread  = ceiling - base

    h30 = Decimal(p.switches.interest_payment[inputs.interest_payment.value])
    h31 = Decimal(p.switches.parcela_frequency[inputs.parcela_frequency.value])
    h32 = Decimal(p.switches.tenor_months[inputs.tenor_months])

    payment_adj = h30 / Decimal(p.scaling_divisors.payment_dim) \
                  * spread * Decimal(str(p.rates.weights.payment_dim))
    parcela_adj = h31 / Decimal(p.scaling_divisors.parcela_dim) \
                  * spread * Decimal(str(p.rates.weights.parcela_dim))
    tenor_adj   = h32 / Decimal(p.scaling_divisors.tenor_dim)   \
                  * spread * Decimal(str(p.rates.weights.tenor_dim))

    return base + payment_adj + parcela_adj + tenor_adj


def annual_to_monthly(rate_pa: Decimal) -> Decimal:
    """Compound: (1 + r_pa)^(1/12) - 1"""
    return (Decimal(1) + rate_pa) ** (Decimal(1) / Decimal(12)) - Decimal(1)
```

### 7.3 Why this formula is the way it is — and a flag

The base+linear-scaling structure is unusual for credit pricing. In production this would normally be a risk-adjusted base + funding spread + OPEX + target margin. **The current formula appears to be a placeholder.** Build it as specified to byte-match the spreadsheet, but isolate it cleanly so it can be replaced without touching anything else. The `compute_nominal_rate_pa` function is the only place this logic should live.

---

## 8. The Schedule Engine

### 8.1 Critical model decision

The Excel models a **bullet-with-optional-coupons** structure: the principal is paid in a single lump at maturity (driven by collateral realization), with optional periodic interest payments in between. The user's choice of "Parcelas" frequency (Monthly / Quarterly / etc.) only controls the **interest payment cadence** — not principal amortization.

**This may not match what the union members actually need.** Standard Brazilian consignado loans use **Tabela Price** (constant total payment, declining interest, rising principal). The simulator may need to support both modes.

**Build both schedule generators** (`bullet_with_coupons` and `tabela_price`), and add an `amortization_method` field to `LoanInputs`. Default to `bullet_with_coupons` (Excel parity) and gate `tabela_price` behind a feature flag for now. Tomás needs to confirm which is the actual product before launch.

### 8.2 Mode A: Bullet-with-coupons (Excel parity)

```python
# src/ccb/engine/schedule.py
def generate_bullet_schedule(
    principal_brl: Decimal,       # face value of CCB (= amount + IOF + fees)
    nominal_rate_pm: Decimal,
    tenor_months: int,
    interest_payment: InterestPayment,
    parcela_frequency: ParcelaFrequency,
    disbursement_date: date,
) -> list[ScheduleRow]:
    """
    Excel rows 174-180.

    Algorithm:
      balance[0] = principal
      For month m in 1..tenor_months:
        accrual[m] = balance[m-1] * rate_pm

        # Interest payment: only if Coupon mode AND m % freq == 0
        if interest_payment == COUPON and m % freq_months(parcela_frequency) == 0:
          interest_pmt[m] = accrued_balance + accrual[m]   # pay accumulated interest
          accrued_balance = 0
        else:
          interest_pmt[m] = 0
          accrued_balance += accrual[m]

        # Principal: bullet at maturity only
        if m == tenor_months:
          principal_pmt[m] = balance[m-1]
          # Plus any accrued interest still on the books
          interest_pmt[m] += accrued_balance
          accrued_balance = 0
        else:
          principal_pmt[m] = 0

        balance[m] = balance[m-1] - principal_pmt[m]
    """
```

`freq_months` mapping: monthly=1, quarterly=3, semiannual=6, annual=12.

**Edge case:** If the loan is `BULLET` (not `COUPON`) — no periodic interest payments at all. Everything (principal + all accrued interest) is paid at month `tenor_months`. The Excel handles this by setting `F172 = 0` for all months when `H30 = 2` (Bullet).

### 8.3 Mode B: Tabela Price (consignado standard) — feature-flagged

```python
def generate_tabela_price_schedule(
    principal_brl: Decimal,
    nominal_rate_pm: Decimal,
    tenor_months: int,
    disbursement_date: date,
) -> list[ScheduleRow]:
    """
    Standard Tabela Price (French amortization).

      PMT = PV * i / (1 - (1+i)^-n)

    For each month:
      interest = balance * i
      principal = PMT - interest
      balance -= principal
    """
    i = nominal_rate_pm
    n = tenor_months
    pmt = principal_brl * i / (Decimal(1) - (Decimal(1) + i) ** Decimal(-n))
    # ... per-month iteration
```

### 8.4 Date generation (EOMONTH equivalent)

The Excel uses `EOMONTH` to roll the disbursement date forward to end-of-each-subsequent-month. Replicate exactly:

```python
# src/ccb/utils/dates.py
from datetime import date
from dateutil.relativedelta import relativedelta

def end_of_month(d: date, months_offset: int = 0) -> date:
    """Excel EOMONTH equivalent."""
    target = d + relativedelta(months=months_offset)
    next_month = target + relativedelta(months=1, day=1)
    return next_month - relativedelta(days=1)
```

---

## 9. CET Calculation

```python
# src/ccb/engine/cet.py
import pyxirr
from decimal import Decimal
from datetime import date

def compute_cet(
    cash_flows: list[Decimal],   # negative = borrower receives, positive = borrower pays
    cash_flow_dates: list[date],
) -> Decimal:
    """
    XIRR over the borrower's gross cash flow.

    Borrower's t=0 cash flow:
      - Receives:  +amount_brl (the disbursement)
      - Pays:      -IOF, -lawyer fee, -BT fee, -bank issuance fee
      Net at t=0:  amount - IOF - fees   (positive = net cash in)

    Note: in our convention, t=0 net is negative-from-lender-perspective
    but positive-from-borrower-perspective. For CET we use the BORROWER
    perspective. Be careful with signs.

    Borrower's t=k cash flows (k > 0):
      - Pays interest_pmt + principal_pmt   (negative)

    Returns annualized rate (CET p.a.).
    """
    rate = pyxirr.xirr(cash_flow_dates, [float(cf) for cf in cash_flows])
    return Decimal(str(rate))
```

**Sign convention warning:** In the Excel, F120 has `-49.47` at t=0 (the FIDC's outflow) and positive values when the borrower pays. The XIRR is taken over this series and gives ~28% (the FIDC's IRR). For CET (borrower's cost), the sign convention is flipped: borrower receives positive at t=0 (the disbursement net of upfront fees) and pays negative thereafter. Either convention gives the same XIRR magnitude — just be consistent in the implementation and test it against the Excel value (35.93% from cell `E134`, see §11).

### 9.1 Building the borrower's CF for CET

```
Borrower's perspective:
  t=0:       +amount_brl
             (the borrower receives the full requested principal;
             IOF and upfront fees are financed into the CCB face value,
             not withheld from disbursement in the workbook model)

  t=1..N:    -interest_payment[t] - principal_payment[t]
             (cash paid to lender; from the schedule)

XIRR of this series, annualized, IS the CET p.a.
CET p.m. = (1 + CET p.a.)^(1/12) - 1
```

The escrow monthly fee (R$ 68/mo) is paid by the **investor side**, not the borrower, so it does NOT enter the borrower's CET calculation. Verify by inspecting Excel: `F114` is in the FIDC cash flow `F120` but the "Net Debtor Cash Flow (CET)" series in row `F128` excludes it. The CET on `E134` is computed from the debtor cash-flow row, where the default scenario is effectively `-45` at `t=0` and `+83.216449...` at month 24 in lender-sign terms. **Implement and verify against E134 = 0.35930.**

---

## 10. API Specification

### 10.1 Public endpoint

```
POST /api/v1/simulate
Content-Type: application/json
```

**Request:**
```json
{
  "amount_brl": 45000,
  "tenor_months": 24,
  "interest_payment": "bullet",
  "parcela_frequency": "monthly",
  "state": "SP",
  "disbursement_date": "2026-04-30"
}
```

**Response (200):**
```json
{
  "nominal_rate_pa": 0.296937,
  "nominal_rate_pm": 0.021904,
  "cet_pa": 0.359301,
  "cet_pm": 0.025911,
  "principal_brl": 45000.00,
  "iof_brl": 1570.83,
  "fees_brl": 2902.50,
  "total_debt_brl": 49473.33,
  "total_paid_brl": 83216.45,
  "total_interest_brl": 38216.45,
  "schedule": [
    {
      "month": 0,
      "date": "2026-04-30",
      "interest_accrual": 0.00,
      "interest_payment": 0.00,
      "principal_payment": 0.00,
      "balance_eop": 49473.33,
      "cash_flow_to_borrower": 45000.00
    },
    {
      "month": 1,
      "date": "2026-05-31",
      "interest_accrual": 1083.64,
      "interest_payment": 0.00,
      "principal_payment": 0.00,
      "balance_eop": 50556.97,
      "cash_flow_to_borrower": 0.00
    }
    /* ... 23 more rows ending at month 24 with the bullet payment of 83216.45 */
  ],
  "inputs": { /* echoed */ }
}
```

**Validation errors (422):** Standard FastAPI/Pydantic — invalid tenor, negative amount, etc.

**Computation errors (400):** If XIRR fails to converge (extremely rare with these inputs):
```json
{ "error": "cet_computation_failed", "detail": "XIRR did not converge" }
```

### 10.2 Internal endpoint (auth-gated)

```
POST /api/v1/internal/analyze
Authorization: Bearer <internal-token>
```

Same request body, but response includes the analytics layer (FIDC IRR, MOIC, duration, CDI+/IPCA+ returns). Implement after the public endpoint is shipping cleanly. Auth via a single shared bearer token from env var for v1.

### 10.3 Health & meta

- `GET /healthz` → `{"status": "ok"}` for k8s/load balancer
- `GET /api/v1/config` → returns the current pricing params (for debugging; gate behind internal auth)

### 10.4 CORS

For v1, allow all origins. Tighten to the production frontend domain at deploy time via env config.

---

## 11. Test Suite — Byte-Match Targets

These values come directly from the Excel workbook with default inputs. **Every test below must pass before the PR is mergeable.** Tolerances: rates to 4 decimal places (0.0001), money values to R$ 0.01.

### 11.1 Default scenario inputs

```
amount_brl       = 45000      (Excel D20 = 45 R$ k)
tenor_months     = 24         (Excel I32)
interest_payment = "bullet"   (Excel I30 → H30 = 2)
parcela_frequency= "monthly"  (Excel I31 → H31 = 1)
```

### 11.2 Pricing engine targets

| Quantity | Excel cell | Expected value | Tolerance |
|---|---|---|---|
| Base rate p.a. | I37 | 0.2670 | exact |
| Ceiling rate p.a. | I38 | 0.335822 | 1e-6 |
| Payment-dim spread | I40 | 0.041293 | 1e-6 |
| Payment adjustment | I41 | 0.020646 | 1e-6 |
| Parcela-dim spread | I43 | 0.020646 | 1e-6 |
| Parcela adjustment | I44 | 0.005162 | 1e-6 |
| Tenor-dim spread | I46 | 0.006882 | 1e-6 |
| Tenor adjustment | I47 | 0.004129 | 1e-6 |
| **Total nominal rate p.a.** | **I49** | **0.296937** | **1e-6** |
| Total nominal rate p.m. | K49 | 0.021904 | 1e-6 |

### 11.3 Money breakdown targets

| Quantity | Excel cell | Expected (BRL) |
|---|---|---|
| Principal | D20 × 1000 | 45,000.00 |
| IOF | F110 × -1000 | 1,570.83 |
| Lawyer origination fee | F106 × -1000 | 1,350.00 |
| BT closing fee | F107 × -1000 | 1,350.00 |
| Bank issuance fee | F108 × -1000 | 202.50 |
| **Total CCB face value** | F180 × 1000 | **49,473.33** |
| Total amortization (bullet at m=24) | H91 | 83,216.45 |

**Implementation note:** `IOF != principal * 3.373%`. To match `F110`, use the gross-up formula from §2.3.

### 11.4 CET targets

| Quantity | Excel cell | Expected | Tolerance |
|---|---|---|---|
| **CET p.a.** | **E134** | **0.359301** | **1e-4** |
| CET p.m. | K50 | 0.025911 | 1e-4 |

### 11.5 Schedule snapshot targets

For `bullet + monthly` mode, balance roll (in BRL):

| Month | Excel ref | balance_eop | interest_accrual |
|---|---|---|---|
| 0 | F180 × 1000 | 49,473.33 | 0.00 |
| 1 | G180 × 1000 | 50,556.97 | 1,083.64 |
| 2 | H180 × 1000 | 51,664.36 | 1,107.38 |
| 3 | I180 × 1000 | 52,795.99 | 1,131.63 |
| 4 | J180 × 1000 | 53,952.41 | 1,156.42 |
| 24 | bullet | balance goes to 0 after payment of 83,216.45 | — |

### 11.6 Coupon-mode test (manual derivation)

The Excel is set to Bullet by default. For Coupon mode (same other inputs), the rate changes because `H30 = 1` instead of 2:

```
payment_adj = 1/4 * spread * 0.60 = 0.010323
total_pa    = 0.267 + 0.010323 + 0.005162 + 0.004129 = 0.286614
total_pm    = (1.286614)^(1/12) - 1 = 0.021185
```

In Coupon + Monthly mode, interest is paid monthly (no accumulation). Each month for m=1..23:
```
interest_payment[m] = 49473.33 * 0.021185 = 1048.08  (approximately, using current balance)
principal_payment[m] = 0
```
At m=24: `principal_payment = 49473.33`, `interest_payment = 1048.08`.

These secondary tests verify the schedule engine handles the COUPON branch correctly. Build a CSV of expected values per month and assert row-by-row.

### 11.7 Test file organization

```python
# tests/test_pricing.py
import pytest
from decimal import Decimal
from ccb.domain.inputs import LoanInputs
from ccb.domain.enums import InterestPayment, ParcelaFrequency
from ccb.engine.pricing import compute_nominal_rate_pa

DEFAULT = LoanInputs(
    amount_brl=Decimal("45000"),
    tenor_months=24,
    interest_payment=InterestPayment.BULLET,
    parcela_frequency=ParcelaFrequency.MONTHLY,
)

def test_default_nominal_rate_pa():
    rate = compute_nominal_rate_pa(DEFAULT)
    assert abs(rate - Decimal("0.296937")) < Decimal("0.000001")

# ... one test function per row in §11.2
```

---

## 12. Configuration & Constants

### 12.1 The YAML approach

All rates, fees, and dimensional weights live in `config/pricing_params.yaml` (template provided in §7.1). Loaded via `pydantic-settings` at startup. To change a rate in production, edit the YAML, rebuild the container, redeploy. **Do not allow runtime mutation of these values via API.**

### 12.2 Environment variables

```
# .env.example
APP_ENV=development                # development | staging | production
PRICING_PARAMS_PATH=./config/pricing_params.yaml
INTERNAL_API_TOKEN=<random-256-bit-hex>
LOG_LEVEL=INFO
CORS_ALLOWED_ORIGINS=*             # tighten in prod
```

---

## 13. Open Questions to Resolve Before Coding

These should be confirmed with Tomás (the product owner) **before** Phase 1 begins. The plan above proceeds with stated assumptions, but validate first:

1. **Is the rate formula final or a placeholder?** Base + linear-scaling-per-dimension is unusual. Confirm with Marcelo/Lucas. (Plan assumes: port as-is, isolate cleanly.)

2. **Tabela Price vs bullet?** Excel models bullet-with-coupons. Standard consignado uses Tabela Price. The plan builds both, defaults to bullet for Excel parity. **Which is the actual product?**

3. **Tenor flexibility.** Excel locks to 12/18/24/30/36. RecargaPay uses a continuous slider. Plan keeps it discrete. Confirm.

4. **CET display granularity.** Display CET p.a. only? Or both p.a. and p.m.? Plan returns both; frontend chooses.

5. **RTD costs.** Currently disabled in Excel (multiplied by 0). Plan implements the lookup but defaults to zero. Confirm whether to absorb or pass through.

6. **Margem consignável.** Pre-simulation, the system needs to verify the requested installment fits within the borrower's payroll margin (typically 35% for consignado). **Where is the source of truth for the union member's payroll?** This blocks production deployment but not the simulator build.

7. **IOF rounding.** Use 3.373% flat (Excel parity) or implement the day-by-day formula? Plan uses flat for v1.

---

## 14. Phasing & Acceptance Criteria

### Phase 1 — Pricing engine + tests (target: 3-4 days)
- [ ] Project skeleton, `pyproject.toml`, `pricing_params.yaml`, settings loading
- [ ] `compute_nominal_rate_pa` implemented
- [ ] All §11.2 tests passing (byte-match)
- [ ] CI green: ruff + mypy --strict + pytest --cov ≥95% on `pricing.py`

### Phase 2 — Schedule + IOF + fees engines (target: 3-4 days)
- [ ] `iof.py` returns 1570.83 for default scenario
- [ ] `fees.py` returns 2902.50 total fees for default scenario
- [ ] `generate_bullet_schedule` returns 25 rows (months 0..24) matching §11.5
- [ ] `generate_tabela_price_schedule` implemented and unit-tested with a known external example
- [ ] Final balance after bullet payment = 0

### Phase 3 — CET (target: 2-3 days)
- [ ] `compute_cet` returns 0.359301 ± 0.0001 for default scenario
- [ ] CET tests for at least 3 other scenarios (different tenors and modes)

### Phase 4 — Public API (target: 2 days)
- [ ] `POST /api/v1/simulate` with full request/response
- [ ] OpenAPI docs render at `/docs`
- [ ] FastAPI TestClient integration tests for happy path + 4 validation failures
- [ ] CORS configured

### Phase 5 — Internal API + analytics stub (target: 2 days)
- [ ] `POST /api/v1/internal/analyze` behind bearer auth
- [ ] Analytics module returns FIDC IRR, MOIC, duration (port from Excel rows 134-139)
- [ ] Macro curves stubbed (return constants) — real BCB integration is later

### Phase 6 — Containerization & deploy-ready (target: 1-2 days)
- [ ] Multi-stage `Dockerfile` (final image < 200MB)
- [ ] `docker-compose.yml` with healthcheck
- [ ] `README.md` with curl examples and local dev instructions
- [ ] GitHub Actions CI: lint + type check + tests on every PR

### Definition of Done (overall)
- All §11 byte-match tests pass
- Test coverage ≥ 90% on `engine/` package
- `mypy --strict` passes with zero errors
- `ruff check` passes with zero errors
- OpenAPI spec validates
- README has working `curl` example that returns the §10.1 sample response

---

## 14a. Design Reference & Frontend Stack

### Layout & visual references

- **Layout reference:** `https://recargapay.com.br/ferramentas/simulador-emprestimo-consignado` — copy the simulator structure (amount input, tenor pills, payment-type toggles, real-time results card, collapsible amortization table).
- **Visual identity reference:** `https://www.btcreditos.com.br/` — extract the design tokens (color palette, typography, button styling, border radii, shadows, spacing) from this site and apply them. Do **not** copy BT Créditos' layout or page structure — only the visual tokens.

### Frontend stack (mandated)

The frontend must be built using the same stack as Prisma's existing internal site:

- **Build tool:** Vite `^8.0.0`
- **Language:** plain HTML, vanilla JavaScript (ES modules), no React/Vue/Next/SPA router
- **Project shape:** multi-page static site (one `.html` per route)
- **Styling:** a single shared stylesheet at `src/style.css` using CSS custom properties — no Tailwind, no Bootstrap, no CSS-in-JS
- **Fonts:** Google Fonts, loaded via `<link>` in each HTML page
- **JS patterns:** `document.getElementById` / `querySelectorAll`, event listeners, `fetch()` to the backend API, no state-management library

Build commands:
```bash
npm install
npm run dev
npm run build
npm run preview
```

### Applying the design tokens within this stack

The agent should fetch `https://www.btcreditos.com.br/`, inspect its CSS and computed styles, and define the extracted tokens as CSS custom properties in `src/style.css`:

```css
:root {
  --color-primary: /* from BT */;
  --color-bg:      /* from BT */;
  --font-family-sans: /* from BT */;
  --radius-md:     /* from BT */;
  /* etc. */
}
```

All component styling in the simulator page consumes these variables. This matches the pattern already used in the reference Prisma site and keeps the design system centrally managed in one file.

### Backend implications

API responses must stay raw (no currency symbols, no thousand separators); locale formatting (`Intl.NumberFormat('pt-BR', ...)`) belongs in the frontend JS. CORS in §10.4 already permits the Vite dev server (`http://localhost:5173`) during development.

---

## 15. Out of Scope (for this build)

These are real and important but **not** part of this backend API. Plan accordingly so they can plug in later:

- Real macro curve integration (BCB SGS API for series 4391/11/433, ANBIMA inflation curve)
- KYC / identity verification (Serpro Datavalid, Receita Federal)
- Union membership verification (specific to each union — likely API integrations)
- Margem consignável check (depends on payroll data source)
- E-signature integration (D4Sign, Clicksign)
- CCB PDF generation (template-based, with QR code)
- Disbursement orchestration (PIX or TED to borrower account)
- Servicing (collection, default tracking, restructuring)
- FIDC integration / cession of receivables
- Investor reporting

For each, ensure the data model has space (e.g., `LoanQuote.id`, `LoanQuote.created_at`, a future `LoanApplication` entity) but do not implement.

---

## 16. Notes for the Coding Agent

1. **Use Decimal, not float, for all money and rate arithmetic.** Floats will silently fail the byte-match tests. The only exception is inside `pyxirr` which expects floats — convert at the boundary and convert back.

2. **Do not invent values.** Every constant comes from §7.1 (which comes from the Excel). If you encounter a calculation that needs a value not in §7.1, stop and flag it rather than guessing.

3. **Keep the engine pure.** No database access, no HTTP calls, no logging side effects inside `engine/`. Logging happens at the API layer.

4. **Sign conventions matter.** The Excel uses lender-perspective signs (negative = lender outflow). The API responses use borrower-perspective for `cash_flow_to_borrower` (positive = borrower receives). Be deliberate and document at function boundaries.

5. **When in doubt, match the Excel.** This document is the spec, but if you find ambiguity, the byte-match tests in §11 are the tiebreaker.

6. **Commit early, commit often.** One commit per phase milestone. PR description should state which §11 tests pass.

---

**End of plan. Build straight through Phases 1-6. Ask before deviating.**
