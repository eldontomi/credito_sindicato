from decimal import Decimal

from ccb.domain.enums import InterestPayment, ParcelaFrequency
from ccb.domain.inputs import LoanInputs
from ccb.engine.pricing import annual_to_monthly, compute_nominal_rate_pa
from ccb.settings import settings

DEFAULT_INPUTS = LoanInputs(
    amount_brl=Decimal("45000"),
    tenor_months=24,
    interest_payment=InterestPayment.BULLET,
    parcela_frequency=ParcelaFrequency.MONTHLY,
)


def assert_close(actual: Decimal, expected: str, tolerance: str) -> None:
    assert abs(actual - Decimal(expected)) < Decimal(tolerance)


def test_pricing_yaml_matches_excel_constants() -> None:
    params = settings.pricing_params

    assert params.rates.base_pa == 0.267
    assert_close(Decimal(str(params.rates.ceiling_pa)), "0.3358215201675907", "0.000000000001")
    assert params.switches.interest_payment["coupon"] == 1
    assert params.switches.interest_payment["bullet"] == 2
    assert params.switches.parcela_frequency["monthly"] == 1
    assert params.switches.tenor_months[24] == 3


def test_default_nominal_rate_pa_matches_excel_i49() -> None:
    rate = compute_nominal_rate_pa(DEFAULT_INPUTS)
    assert_close(rate, "0.296937361272902", "0.000001")


def test_default_nominal_rate_pm_matches_excel_k49() -> None:
    monthly_rate = annual_to_monthly(compute_nominal_rate_pa(DEFAULT_INPUTS))
    assert_close(monthly_rate, "0.021903570988894172", "0.000001")


def test_default_pricing_components_match_excel() -> None:
    params = settings.pricing_params
    spread = Decimal(str(params.rates.ceiling_pa)) - Decimal(str(params.rates.base_pa))

    payment_dim_spread = spread * Decimal(str(params.rates.weights.payment_dim))
    payment_adjustment = Decimal("2") / Decimal("4") * payment_dim_spread
    parcela_dim_spread = spread * Decimal(str(params.rates.weights.parcela_dim))
    parcela_adjustment = Decimal("1") / Decimal("4") * parcela_dim_spread
    tenor_dim_spread = spread * Decimal(str(params.rates.weights.tenor_dim))
    tenor_adjustment = Decimal("3") / Decimal("5") * tenor_dim_spread

    assert_close(payment_dim_spread, "0.041292912100554413", "0.000001")
    assert_close(payment_adjustment, "0.020646456050277207", "0.000001")
    assert_close(parcela_dim_spread, "0.020646456050277207", "0.000001")
    assert_close(parcela_adjustment, "0.005161614012569302", "0.000001")
    assert_close(tenor_dim_spread, "0.006882152016759069", "0.000001")
    assert_close(tenor_adjustment, "0.004129291210055441", "0.000001")


def test_coupon_monthly_scenario_matches_manual_derivation() -> None:
    coupon_inputs = LoanInputs(
        amount_brl=Decimal("45000"),
        tenor_months=24,
        interest_payment=InterestPayment.COUPON,
        parcela_frequency=ParcelaFrequency.MONTHLY,
    )

    rate_pa = compute_nominal_rate_pa(coupon_inputs)
    rate_pm = annual_to_monthly(rate_pa)

    assert_close(rate_pa, "0.28661413324776336", "0.000001")
    assert_close(rate_pm, "0.021223248586474904", "0.000001")
