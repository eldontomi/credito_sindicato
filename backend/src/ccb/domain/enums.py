from enum import StrEnum


class InterestPayment(StrEnum):
    COUPON = "coupon"
    BULLET = "bullet"


class ParcelaFrequency(StrEnum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMIANNUAL = "semiannual"
    ANNUAL = "annual"


class State(StrEnum):
    SP = "SP"
    RJ = "RJ"


class AmortizationMethod(StrEnum):
    BULLET_WITH_COUPONS = "bullet_with_coupons"
    TABELA_PRICE = "tabela_price"
