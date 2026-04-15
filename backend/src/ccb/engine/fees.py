from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from ccb.settings import settings


def _decimal(value: float | int | str) -> Decimal:
    return Decimal(str(value))


class FeeBreakdown(BaseModel):
    lawyer_origination_brl: Decimal
    bt_closing_brl: Decimal
    bank_issuance_brl: Decimal
    rtd_register_brl: Decimal

    @property
    def total_brl(self) -> Decimal:
        return (
            self.lawyer_origination_brl
            + self.bt_closing_brl
            + self.bank_issuance_brl
            + self.rtd_register_brl
        )


def compute_fee_breakdown(amount_brl: Decimal) -> FeeBreakdown:
    fees = settings.pricing_params.fees

    lawyer_origination_brl = amount_brl * _decimal(fees.lawyer_origination_pct)
    bt_closing_brl = amount_brl * _decimal(fees.bt_closing_pct)
    bank_issuance_brl = max(
        amount_brl * _decimal(fees.bank_issuance_pct_flat),
        _decimal(fees.bank_issuance_min_brl),
    )
    rtd_register_brl = _decimal(fees.rtd_register_brl)

    return FeeBreakdown(
        lawyer_origination_brl=lawyer_origination_brl,
        bt_closing_brl=bt_closing_brl,
        bank_issuance_brl=bank_issuance_brl,
        rtd_register_brl=rtd_register_brl,
    )

