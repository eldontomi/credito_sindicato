from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from ccb.domain.outputs import AnalyticsResult, LoanQuote

RATE_QUANTUM = Decimal("0.000001")


def quantize_rate(value: Decimal) -> Decimal:
    return value.quantize(RATE_QUANTUM, rounding=ROUND_HALF_UP)


def build_analytics_stub(quote: LoanQuote) -> AnalyticsResult:
    total_paid = quote.total_paid_brl
    total_debt = quote.total_debt_brl

    moic = total_paid / total_debt if total_debt != 0 else Decimal("0")
    duration_months = Decimal(str(quote.inputs.tenor_months))

    return AnalyticsResult(
        fidc_irr_pa=quote.cet_pa,
        debtor_irr_pa=quote.cet_pa,
        moic=quantize_rate(moic),
        duration_months=duration_months,
        cdi_plus_annualized=Decimal("0"),
        ipca_plus_annualized=Decimal("0"),
    )

