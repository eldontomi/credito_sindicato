from __future__ import annotations

from datetime import date
from decimal import Decimal

import pyxirr

from ccb.domain.outputs import ScheduleRow


def compute_cet(cash_flows: list[Decimal], cash_flow_dates: list[date]) -> Decimal:
    if len(cash_flows) != len(cash_flow_dates):
        msg = "cash_flows and cash_flow_dates must have the same length"
        raise ValueError(msg)

    rate = pyxirr.xirr(cash_flow_dates, [float(cash_flow) for cash_flow in cash_flows])
    return Decimal(str(rate))


def annual_to_monthly_effective(rate_pa: Decimal) -> Decimal:
    return (Decimal(1) + rate_pa) ** (Decimal(1) / Decimal(12)) - Decimal(1)


def borrower_cash_flows_from_schedule(
    schedule: list[ScheduleRow],
) -> tuple[list[Decimal], list[date]]:
    non_zero_rows = [row for row in schedule if row.cash_flow_to_borrower != 0]
    cash_flows = [row.cash_flow_to_borrower for row in non_zero_rows]
    cash_flow_dates = [row.date for row in non_zero_rows]
    return cash_flows, cash_flow_dates
