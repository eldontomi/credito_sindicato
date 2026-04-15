from __future__ import annotations

from functools import cached_property
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RateWeights(BaseModel):
    payment_dim: float
    parcela_dim: float
    tenor_dim: float


class RatesConfig(BaseModel):
    base_pa: float
    ceiling_pa: float
    weights: RateWeights


class SwitchesConfig(BaseModel):
    interest_payment: dict[str, int]
    parcela_frequency: dict[str, int]
    tenor_months: dict[int, int]


class ScalingDivisorsConfig(BaseModel):
    payment_dim: int
    parcela_dim: int
    tenor_dim: int


class FeesConfig(BaseModel):
    lawyer_origination_pct: float
    bt_closing_pct: float
    bank_issuance_pct_flat: float
    bank_issuance_min_brl: float
    escrow_opening_brl: float
    escrow_monthly_brl: float
    rtd_register_brl: float


class TaxesConfig(BaseModel):
    iof_total_pct: float


class PricingParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rates: RatesConfig
    switches: SwitchesConfig
    scaling_divisors: ScalingDivisorsConfig
    fees: FeesConfig
    taxes: TaxesConfig


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    pricing_params_path: Path = Field(default=Path("./config/pricing_params.yaml"))
    internal_api_token: str = "replace-me"
    log_level: str = "INFO"
    cors_allowed_origins: str = "*"

    @cached_property
    def pricing_params(self) -> PricingParams:
        raw = yaml.safe_load(self.pricing_params_path.read_text(encoding="utf-8"))
        return PricingParams.model_validate(raw)


settings = AppSettings()
