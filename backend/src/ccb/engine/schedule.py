from __future__ import annotations

from datetime import date
from decimal import Decimal

from ccb.domain.enums import InterestPayment, ParcelaFrequency
from ccb.domain.outputs import ScheduleRow
from ccb.utils.dates import end_of_month


def _decimal(value: float | int | str) -> Decimal:
    return Decimal(str(value))


def frequency_months(parcela_frequency: ParcelaFrequency) -> int:
    return {
        ParcelaFrequency.MONTHLY: 1,
        ParcelaFrequency.QUARTERLY: 3,
        ParcelaFrequency.SEMIANNUAL: 6,
        ParcelaFrequency.ANNUAL: 12,
    }[parcela_frequency]


def generate_bullet_schedule(
    principal_brl: Decimal,
    nominal_rate_pm: Decimal,
    tenor_months: int,
    interest_payment: InterestPayment,
    parcela_frequency: ParcelaFrequency,
    disbursement_date: date,
    net_disbursement_brl: Decimal,
) -> list[ScheduleRow]:
    rows = [
        ScheduleRow(
            month=0,
            date=disbursement_date,
            interest_accrual=Decimal("0"),
            interest_payment=Decimal("0"),
            principal_payment=Decimal("0"),
            balance_eop=principal_brl,
            cash_flow_to_borrower=net_disbursement_brl,
        )
    ]

    accrued_unpaid_interest = Decimal("0")
    opening_balance = principal_brl
    payment_frequency = frequency_months(parcela_frequency)

    for month in range(1, tenor_months + 1):
        interest_accrual = opening_balance * nominal_rate_pm
        current_period_interest_payment = Decimal("0")

        if (
            interest_payment is InterestPayment.COUPON
            and month % payment_frequency == 0
        ):
            current_period_interest_payment = accrued_unpaid_interest + interest_accrual
            accrued_unpaid_interest = Decimal("0")
        else:
            accrued_unpaid_interest += interest_accrual

        principal_payment = Decimal("0")
        if month == tenor_months:
            principal_payment = principal_brl
            current_period_interest_payment = (
                opening_balance + interest_accrual - principal_payment
            )
            accrued_unpaid_interest = Decimal("0")

        closing_balance = (
            opening_balance
            + interest_accrual
            - current_period_interest_payment
            - principal_payment
        )

        rows.append(
            ScheduleRow(
                month=month,
                date=end_of_month(disbursement_date, month),
                interest_accrual=interest_accrual,
                interest_payment=current_period_interest_payment,
                principal_payment=principal_payment,
                balance_eop=closing_balance,
                cash_flow_to_borrower=-(current_period_interest_payment + principal_payment),
            )
        )
        opening_balance = closing_balance

    return rows


def generate_tabela_price_schedule(
    principal_brl: Decimal,
    nominal_rate_pm: Decimal,
    tenor_months: int,
    disbursement_date: date,
    net_disbursement_brl: Decimal | None = None,
) -> list[ScheduleRow]:
    installment_brl = principal_brl * nominal_rate_pm / (
        Decimal(1) - (Decimal(1) + nominal_rate_pm) ** Decimal(-tenor_months)
    )
    rows = [
        ScheduleRow(
            month=0,
            date=disbursement_date,
            interest_accrual=Decimal("0"),
            interest_payment=Decimal("0"),
            principal_payment=Decimal("0"),
            balance_eop=principal_brl,
            cash_flow_to_borrower=(
                principal_brl if net_disbursement_brl is None else net_disbursement_brl
            ),
        )
    ]

    opening_balance = principal_brl
    for month in range(1, tenor_months + 1):
        interest_accrual = opening_balance * nominal_rate_pm
        principal_payment = installment_brl - interest_accrual
        closing_balance = opening_balance - principal_payment
        if month == tenor_months:
            principal_payment += closing_balance
            closing_balance = Decimal("0")
        rows.append(
            ScheduleRow(
                month=month,
                date=end_of_month(disbursement_date, month),
                interest_accrual=interest_accrual,
                interest_payment=interest_accrual,
                principal_payment=principal_payment,
                balance_eop=closing_balance,
                cash_flow_to_borrower=-(interest_accrual + principal_payment),
            )
        )
        opening_balance = closing_balance

    return rows
