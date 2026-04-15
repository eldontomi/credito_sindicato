from __future__ import annotations

from decimal import Decimal

from ccb.domain.inputs import LoanInputs
from ccb.settings import settings


def _decimal(value: float | int | str) -> Decimal:
    return Decimal(str(value))


def compute_nominal_rate_pa(inputs: LoanInputs) -> Decimal:
    pricing_params = settings.pricing_params

    base = _decimal(pricing_params.rates.base_pa)
    ceiling = _decimal(pricing_params.rates.ceiling_pa)
    spread = ceiling - base

    interest_payment_switch = _decimal(
        pricing_params.switches.interest_payment[inputs.interest_payment.value]
    )
    parcela_frequency_switch = _decimal(
        pricing_params.switches.parcela_frequency[inputs.parcela_frequency.value]
    )
    tenor_switch = _decimal(pricing_params.switches.tenor_months[inputs.tenor_months])

    payment_adj = (
        interest_payment_switch
        / _decimal(pricing_params.scaling_divisors.payment_dim)
        * spread
        * _decimal(pricing_params.rates.weights.payment_dim)
    )
    parcela_adj = (
        parcela_frequency_switch
        / _decimal(pricing_params.scaling_divisors.parcela_dim)
        * spread
        * _decimal(pricing_params.rates.weights.parcela_dim)
    )
    tenor_adj = (
        tenor_switch
        / _decimal(pricing_params.scaling_divisors.tenor_dim)
        * spread
        * _decimal(pricing_params.rates.weights.tenor_dim)
    )

    return base + payment_adj + parcela_adj + tenor_adj


def annual_to_monthly(rate_pa: Decimal) -> Decimal:
    return (Decimal(1) + rate_pa) ** (Decimal(1) / Decimal(12)) - Decimal(1)

