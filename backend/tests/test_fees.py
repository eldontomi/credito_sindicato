from decimal import ROUND_HALF_UP, Decimal

from ccb.engine.fees import compute_fee_breakdown


def quantize_brl(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def test_default_fee_breakdown_matches_workbook() -> None:
    fees = compute_fee_breakdown(Decimal("45000"))

    assert quantize_brl(fees.lawyer_origination_brl) == Decimal("1350.00")
    assert quantize_brl(fees.bt_closing_brl) == Decimal("1350.00")
    assert quantize_brl(fees.bank_issuance_brl) == Decimal("202.50")
    assert quantize_brl(fees.rtd_register_brl) == Decimal("0.00")
    assert quantize_brl(fees.total_brl) == Decimal("2902.50")

