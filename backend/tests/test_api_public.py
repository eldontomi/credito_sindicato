from __future__ import annotations

from fastapi.testclient import TestClient

from ccb.main import app

client = TestClient(app)


def test_simulate_endpoint_happy_path() -> None:
    response = client.post(
        "/api/v1/simulate",
        json={
            "amount_brl": 45000,
            "tenor_months": 24,
            "interest_payment": "bullet",
            "parcela_frequency": "monthly",
            "state": "SP",
            "disbursement_date": "2026-03-31",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["nominal_rate_pa"] == "0.296937"
    assert data["nominal_rate_pm"] == "0.021904"
    assert data["cet_pa"] == "0.359301"
    assert data["cet_pm"] == "0.025911"
    assert data["principal_brl"] == "45000.00"
    assert data["iof_brl"] == "1570.83"
    assert data["fees_brl"] == "2902.50"
    assert data["total_debt_brl"] == "49473.33"
    assert data["total_paid_brl"] == "83216.45"
    assert data["total_interest_brl"] == "38216.45"
    assert len(data["schedule"]) == 25
    assert data["schedule"][0]["cash_flow_to_borrower"] == "45000.00"
    assert data["schedule"][24]["interest_payment"] == "33743.12"
    assert data["schedule"][24]["principal_payment"] == "49473.33"
    assert data["schedule"][24]["balance_eop"] == "0.00"


def test_simulate_endpoint_rejects_invalid_tenor() -> None:
    response = client.post(
        "/api/v1/simulate",
        json={
            "amount_brl": 45000,
            "tenor_months": 20,
            "interest_payment": "bullet",
            "parcela_frequency": "monthly",
        },
    )

    assert response.status_code == 422


def test_simulate_endpoint_rejects_negative_amount() -> None:
    response = client.post(
        "/api/v1/simulate",
        json={
            "amount_brl": -1,
            "tenor_months": 24,
            "interest_payment": "bullet",
            "parcela_frequency": "monthly",
        },
    )

    assert response.status_code == 422


def test_simulate_endpoint_rejects_unknown_interest_payment() -> None:
    response = client.post(
        "/api/v1/simulate",
        json={
            "amount_brl": 45000,
            "tenor_months": 24,
            "interest_payment": "foo",
            "parcela_frequency": "monthly",
        },
    )

    assert response.status_code == 422


def test_simulate_endpoint_rejects_amount_above_limit() -> None:
    response = client.post(
        "/api/v1/simulate",
        json={
            "amount_brl": 1000001,
            "tenor_months": 24,
            "interest_payment": "bullet",
            "parcela_frequency": "monthly",
        },
    )

    assert response.status_code == 422
