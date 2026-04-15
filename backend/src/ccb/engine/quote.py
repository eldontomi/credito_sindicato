from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from ccb.domain.enums import AmortizationMethod
from ccb.domain.inputs import LoanInputs
from ccb.domain.outputs import LoanQuote, ScheduleRow
from ccb.engine.cet import (
    annual_to_monthly_effective,
    borrower_cash_flows_from_schedule,
    compute_cet,
)
from ccb.engine.fees import compute_fee_breakdown
from ccb.engine.iof import compute_iof_brl
from ccb.engine.pricing import annual_to_monthly, compute_nominal_rate_pa
from ccb.engine.schedule import (
    generate_bullet_schedule,
    generate_tabela_price_schedule,
)

BRL_QUANTUM = Decimal("0.01")
RATE_QUANTUM = Decimal("0.000001")


def quantize_brl(value: Decimal) -> Decimal:
    return value.quantize(BRL_QUANTUM, rounding=ROUND_HALF_UP)


def quantize_rate(value: Decimal) -> Decimal:
    return value.quantize(RATE_QUANTUM, rounding=ROUND_HALF_UP)


def resolve_disbursement_date(value: date | None) -> date:
    return date.today() if value is None else value


def build_loan_quote(inputs: LoanInputs) -> LoanQuote:
    disbursement_date = resolve_disbursement_date(inputs.disbursement_date)
    resolved_inputs = inputs.model_copy(update={"disbursement_date": disbursement_date})

    nominal_rate_pa = compute_nominal_rate_pa(resolved_inputs)
    nominal_rate_pm = annual_to_monthly(nominal_rate_pa)
    fees = compute_fee_breakdown(resolved_inputs.amount_brl)
    iof_brl = compute_iof_brl(resolved_inputs.amount_brl)
    total_debt_brl = resolved_inputs.amount_brl + fees.total_brl + iof_brl

    if resolved_inputs.amortization_method is AmortizationMethod.BULLET_WITH_COUPONS:
        raw_schedule = generate_bullet_schedule(
            principal_brl=total_debt_brl,
            nominal_rate_pm=nominal_rate_pm,
            tenor_months=resolved_inputs.tenor_months,
            interest_payment=resolved_inputs.interest_payment,
            parcela_frequency=resolved_inputs.parcela_frequency,
            disbursement_date=disbursement_date,
            net_disbursement_brl=resolved_inputs.amount_brl,
        )
    else:
        raw_schedule = generate_tabela_price_schedule(
            principal_brl=total_debt_brl,
            nominal_rate_pm=nominal_rate_pm,
            tenor_months=resolved_inputs.tenor_months,
            disbursement_date=disbursement_date,
            net_disbursement_brl=resolved_inputs.amount_brl,
        )

    cash_flows, cash_flow_dates = borrower_cash_flows_from_schedule(raw_schedule)
    cet_pa = compute_cet(cash_flows, cash_flow_dates)
    cet_pm = annual_to_monthly_effective(cet_pa)

    total_paid_brl = -sum(
        (
            row.cash_flow_to_borrower
            for row in raw_schedule[1:]
            if row.cash_flow_to_borrower < 0
        ),
        Decimal("0"),
    )
    total_interest_brl = total_paid_brl - resolved_inputs.amount_brl

    schedule = [quantize_schedule_row(row) for row in raw_schedule]

    return LoanQuote(
        nominal_rate_pa=quantize_rate(nominal_rate_pa),
        nominal_rate_pm=quantize_rate(nominal_rate_pm),
        cet_pa=quantize_rate(cet_pa),
        cet_pm=quantize_rate(cet_pm),
        principal_brl=quantize_brl(resolved_inputs.amount_brl),
        iof_brl=quantize_brl(iof_brl),
        fees_brl=quantize_brl(fees.total_brl),
        total_debt_brl=quantize_brl(total_debt_brl),
        total_paid_brl=quantize_brl(total_paid_brl),
        total_interest_brl=quantize_brl(total_interest_brl),
        schedule=schedule,
        inputs=resolved_inputs,
    )


def quantize_schedule_row(row: ScheduleRow) -> ScheduleRow:
    return row.model_copy(
        update={
            "interest_accrual": quantize_brl(row.interest_accrual),
            "interest_payment": quantize_brl(row.interest_payment),
            "principal_payment": quantize_brl(row.principal_payment),
            "balance_eop": quantize_brl(row.balance_eop),
            "cash_flow_to_borrower": quantize_brl(row.cash_flow_to_borrower),
        }
    )
