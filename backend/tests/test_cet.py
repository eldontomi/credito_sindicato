from datetime import date
from decimal import Decimal

from ccb.domain.enums import InterestPayment, ParcelaFrequency
from ccb.domain.inputs import LoanInputs
from ccb.engine.cet import (
    annual_to_monthly_effective,
    borrower_cash_flows_from_schedule,
    compute_cet,
)
from ccb.engine.fees import compute_fee_breakdown
from ccb.engine.iof import compute_iof_brl
from ccb.engine.pricing import annual_to_monthly, compute_nominal_rate_pa
from ccb.engine.schedule import generate_bullet_schedule


def build_face_value(amount_brl: Decimal) -> Decimal:
    fees = compute_fee_breakdown(amount_brl)
    iof_brl = compute_iof_brl(amount_brl)
    return amount_brl + fees.total_brl + iof_brl


def build_bullet_schedule(inputs: LoanInputs) -> list:
    rate_pm = annual_to_monthly(compute_nominal_rate_pa(inputs))
    return generate_bullet_schedule(
        principal_brl=build_face_value(inputs.amount_brl),
        nominal_rate_pm=rate_pm,
        tenor_months=inputs.tenor_months,
        interest_payment=inputs.interest_payment,
        parcela_frequency=inputs.parcela_frequency,
        disbursement_date=date(2026, 3, 31),
        net_disbursement_brl=inputs.amount_brl,
    )


def test_default_cet_matches_workbook_e134() -> None:
    inputs = LoanInputs(
        amount_brl=Decimal("45000"),
        tenor_months=24,
        interest_payment=InterestPayment.BULLET,
        parcela_frequency=ParcelaFrequency.MONTHLY,
    )
    schedule = build_bullet_schedule(inputs)
    cash_flows, cash_flow_dates = borrower_cash_flows_from_schedule(schedule)

    cet_pa = compute_cet(cash_flows, cash_flow_dates)
    cet_pm = annual_to_monthly_effective(cet_pa)

    assert abs(cet_pa - Decimal("0.35930122733116154")) < Decimal("0.0001")
    assert abs(cet_pm - Decimal("0.025910896050664434")) < Decimal("0.0001")


def test_cet_is_sign_invariant_in_magnitude() -> None:
    inputs = LoanInputs(
        amount_brl=Decimal("45000"),
        tenor_months=24,
        interest_payment=InterestPayment.BULLET,
        parcela_frequency=ParcelaFrequency.MONTHLY,
    )
    schedule = build_bullet_schedule(inputs)
    cash_flows, cash_flow_dates = borrower_cash_flows_from_schedule(schedule)

    borrower_cet = compute_cet(cash_flows, cash_flow_dates)
    lender_cet = compute_cet([-cash_flow for cash_flow in cash_flows], cash_flow_dates)

    assert abs(borrower_cet - lender_cet) < Decimal("0.0000001")


def test_coupon_mode_cet_exceeds_nominal_rate() -> None:
    inputs = LoanInputs(
        amount_brl=Decimal("45000"),
        tenor_months=24,
        interest_payment=InterestPayment.COUPON,
        parcela_frequency=ParcelaFrequency.MONTHLY,
    )
    schedule = build_bullet_schedule(inputs)
    cash_flows, cash_flow_dates = borrower_cash_flows_from_schedule(schedule)

    cet_pa = compute_cet(cash_flows, cash_flow_dates)
    nominal_pa = compute_nominal_rate_pa(inputs)

    assert cet_pa > nominal_pa
