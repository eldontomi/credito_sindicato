from __future__ import annotations

from fastapi.testclient import TestClient

from ccb.main import app
from ccb.settings import settings

client = TestClient(app)


def auth_header() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.internal_api_token}"}


def test_internal_analyze_requires_auth() -> None:
    response = client.post(
        "/api/v1/internal/analyze",
        json={
            "amount_brl": 45000,
            "tenor_months": 24,
            "interest_payment": "bullet",
            "parcela_frequency": "monthly",
        },
    )

    assert response.status_code == 401


def test_internal_analyze_rejects_wrong_token() -> None:
    response = client.post(
        "/api/v1/internal/analyze",
        headers={"Authorization": "Bearer wrong-token"},
        json={
            "amount_brl": 45000,
            "tenor_months": 24,
            "interest_payment": "bullet",
            "parcela_frequency": "monthly",
        },
    )

    assert response.status_code == 401


def test_internal_analyze_happy_path_returns_quote_and_analytics() -> None:
    response = client.post(
        "/api/v1/internal/analyze",
        headers=auth_header(),
        json={
            "amount_brl": 45000,
            "tenor_months": 24,
            "interest_payment": "bullet",
            "parcela_frequency": "monthly",
            "disbursement_date": "2026-03-31",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "quote" in data
    assert "analytics" in data
    assert data["quote"]["cet_pa"] == "0.359301"
    assert data["analytics"]["fidc_irr_pa"] == "0.359301"
    assert data["analytics"]["debtor_irr_pa"] == "0.359301"
    assert data["analytics"]["moic"] == "1.682047"
    assert data["analytics"]["duration_months"] == "24"
    assert data["analytics"]["cdi_plus_annualized"] == "0"
    assert data["analytics"]["ipca_plus_annualized"] == "0"
