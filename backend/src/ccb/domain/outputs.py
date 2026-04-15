from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from ccb.domain.inputs import LoanInputs


class ScheduleRow(BaseModel):
    month: int
    date: date
    interest_accrual: Decimal
    interest_payment: Decimal
    principal_payment: Decimal
    balance_eop: Decimal
    cash_flow_to_borrower: Decimal


class LoanQuote(BaseModel):
    nominal_rate_pa: Decimal
    nominal_rate_pm: Decimal
    cet_pa: Decimal
    cet_pm: Decimal
    principal_brl: Decimal
    iof_brl: Decimal
    fees_brl: Decimal
    total_debt_brl: Decimal
    total_paid_brl: Decimal
    total_interest_brl: Decimal
    schedule: list[ScheduleRow]
    inputs: LoanInputs


class AnalyticsResult(BaseModel):
    fidc_irr_pa: Decimal
    debtor_irr_pa: Decimal
    moic: Decimal
    duration_months: Decimal
    cdi_plus_annualized: Decimal
    ipca_plus_annualized: Decimal


class InternalAnalysisResult(BaseModel):
    quote: LoanQuote
    analytics: AnalyticsResult
