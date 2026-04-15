from __future__ import annotations

from datetime import date

from dateutil.relativedelta import relativedelta


def end_of_month(value: date, months_offset: int = 0) -> date:
    target = value + relativedelta(months=months_offset)
    next_month = target + relativedelta(months=1, day=1)
    return next_month - relativedelta(days=1)

