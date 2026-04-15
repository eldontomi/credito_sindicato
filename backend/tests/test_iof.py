from decimal import ROUND_HALF_UP, Decimal

from ccb.engine.iof import compute_iof_brl


def quantize_brl(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def test_default_iof_matches_workbook() -> None:
    iof_brl = compute_iof_brl(Decimal("45000"))
    assert quantize_brl(iof_brl) == Decimal("1570.83")


def test_iof_uses_gross_up_not_flat_percentage() -> None:
    iof_brl = compute_iof_brl(Decimal("45000"))
    assert iof_brl > Decimal("1517.85")

