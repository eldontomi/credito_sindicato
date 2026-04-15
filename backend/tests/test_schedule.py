from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from ccb.domain.enums import InterestPayment, ParcelaFrequency
from ccb.domain.inputs import LoanInputs
from ccb.engine.fees import compute_fee_breakdown
from ccb.engine.iof import compute_iof_brl
from ccb.engine.pricing import annual_to_monthly, compute_nominal_rate_pa
from ccb.engine.schedule import generate_bullet_schedule, generate_tabela_price_schedule


def quantize_brl(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


DEFAULT_INPUTS = LoanInputs(
    amount_brl=Decimal("45000"),
    tenor_months=24,
    interest_payment=InterestPayment.BULLET,
    parcela_frequency=ParcelaFrequency.MONTHLY,
)


def build_default_face_value() -> Decimal:
    fees = compute_fee_breakdown(DEFAULT_INPUTS.amount_brl)
    iof_brl = compute_iof_brl(DEFAULT_INPUTS.amount_brl)
    return DEFAULT_INPUTS.amount_brl + fees.total_brl + iof_brl


def test_bullet_schedule_matches_workbook_snapshot() -> None:
    rate_pm = annual_to_monthly(compute_nominal_rate_pa(DEFAULT_INPUTS))
    schedule = generate_bullet_schedule(
        principal_brl=build_default_face_value(),
        nominal_rate_pm=rate_pm,
        tenor_months=DEFAULT_INPUTS.tenor_months,
        interest_payment=DEFAULT_INPUTS.interest_payment,
        parcela_frequency=DEFAULT_INPUTS.parcela_frequency,
        disbursement_date=date(2026, 3, 31),
        net_disbursement_brl=DEFAULT_INPUTS.amount_brl,
    )

    assert len(schedule) == 25
    assert quantize_brl(schedule[0].balance_eop) == Decimal("49473.33")
    assert quantize_brl(schedule[1].balance_eop) == Decimal("50556.98")
    assert quantize_brl(schedule[1].interest_accrual) == Decimal("1083.64")
    assert quantize_brl(schedule[2].balance_eop) == Decimal("51664.36")
    assert quantize_brl(schedule[2].interest_accrual) == Decimal("1107.38")
    assert quantize_brl(schedule[3].balance_eop) == Decimal("52795.99")
    assert quantize_brl(schedule[3].interest_accrual) == Decimal("1131.63")
    assert quantize_brl(schedule[4].balance_eop) == Decimal("53952.41")
    assert quantize_brl(schedule[4].interest_accrual) == Decimal("1156.42")
    assert quantize_brl(schedule[24].interest_payment + schedule[24].principal_payment) == Decimal(
        "83216.45"
    )
    assert quantize_brl(schedule[24].balance_eop) == Decimal("0.00")


def test_coupon_monthly_schedule_pays_interest_monthly() -> None:
    inputs = LoanInputs(
        amount_brl=Decimal("45000"),
        tenor_months=24,
        interest_payment=InterestPayment.COUPON,
        parcela_frequency=ParcelaFrequency.MONTHLY,
    )
    rate_pm = annual_to_monthly(compute_nominal_rate_pa(inputs))
    face_value = (
        inputs.amount_brl
        + compute_fee_breakdown(inputs.amount_brl).total_brl
        + compute_iof_brl(inputs.amount_brl)
    )
    schedule = generate_bullet_schedule(
        principal_brl=face_value,
        nominal_rate_pm=rate_pm,
        tenor_months=inputs.tenor_months,
        interest_payment=inputs.interest_payment,
        parcela_frequency=inputs.parcela_frequency,
        disbursement_date=date(2026, 3, 31),
        net_disbursement_brl=inputs.amount_brl,
    )

    assert quantize_brl(schedule[1].interest_payment) == Decimal("1049.98")
    assert quantize_brl(schedule[1].principal_payment) == Decimal("0.00")
    assert quantize_brl(schedule[1].balance_eop) == Decimal("49473.33")
    assert quantize_brl(schedule[24].principal_payment) == Decimal("49473.33")
    assert quantize_brl(schedule[24].interest_payment) == Decimal("1049.98")
    assert quantize_brl(schedule[24].balance_eop) == Decimal("0.00")


def test_tabela_price_schedule_amortizes_to_zero() -> None:
    schedule = generate_tabela_price_schedule(
        principal_brl=Decimal("1000"),
        nominal_rate_pm=Decimal("0.01"),
        tenor_months=3,
        disbursement_date=date(2026, 1, 31),
    )

    assert len(schedule) == 4
    assert quantize_brl(schedule[1].interest_payment) == Decimal("10.00")
    assert quantize_brl(schedule[1].principal_payment) == Decimal("330.02")
    assert quantize_brl(schedule[1].balance_eop) == Decimal("669.98")
    assert quantize_brl(schedule[3].balance_eop) == Decimal("0.00")
