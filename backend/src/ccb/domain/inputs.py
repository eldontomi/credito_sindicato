from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from ccb.domain.enums import (
    AmortizationMethod,
    InterestPayment,
    ParcelaFrequency,
    State,
)


class LoanInputs(BaseModel):
    amount_brl: Decimal = Field(..., gt=Decimal("0"), le=Decimal("1000000"))
    tenor_months: int
    interest_payment: InterestPayment
    parcela_frequency: ParcelaFrequency
    amortization_method: AmortizationMethod = AmortizationMethod.BULLET_WITH_COUPONS
    state: State = State.SP
    disbursement_date: date | None = None

    @field_validator("tenor_months")
    @classmethod
    def validate_tenor_months(cls, value: int) -> int:
        if value not in (12, 18, 24, 30, 36):
            msg = "tenor_months must be one of: 12, 18, 24, 30, 36"
            raise ValueError(msg)
        return value

