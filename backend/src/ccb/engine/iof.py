from __future__ import annotations

from decimal import Decimal

from ccb.settings import settings


def _decimal(value: float | int | str) -> Decimal:
    return Decimal(str(value))


def compute_iof_brl(amount_brl: Decimal) -> Decimal:
    """Excel-parity IOF gross-up for v1.

    The workbook finances IOF into the CCB face value so the borrower still
    receives the requested principal amount at disbursement.
    """

    iof_total_pct = _decimal(settings.pricing_params.taxes.iof_total_pct)
    return amount_brl * ((Decimal(1) / (Decimal(1) - iof_total_pct)) - Decimal(1))

