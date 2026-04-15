from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ccb.domain.inputs import LoanInputs
from ccb.domain.outputs import LoanQuote
from ccb.engine.quote import build_loan_quote

router = APIRouter(prefix="/api/v1", tags=["public"])


@router.post("/simulate", response_model=LoanQuote)
def simulate_loan(inputs: LoanInputs) -> LoanQuote:
    try:
        return build_loan_quote(inputs)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "cet_computation_failed", "detail": str(exc)},
        ) from exc

