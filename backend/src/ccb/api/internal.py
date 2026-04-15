from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status

from ccb.domain.inputs import LoanInputs
from ccb.domain.outputs import InternalAnalysisResult, LoanQuote
from ccb.engine.analytics import build_analytics_stub
from ccb.engine.quote import build_loan_quote
from ccb.settings import settings

router = APIRouter(prefix="/api/v1/internal", tags=["internal"])


def require_internal_bearer_token(
    authorization: str | None = Header(default=None),
) -> None:
    expected = f"Bearer {settings.internal_api_token}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
        )


@router.post(
    "/analyze",
    response_model=InternalAnalysisResult,
    dependencies=[Depends(require_internal_bearer_token)],
)
def analyze_loan(inputs: LoanInputs) -> InternalAnalysisResult:
    try:
        quote: LoanQuote = build_loan_quote(inputs)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "cet_computation_failed", "detail": str(exc)},
        ) from exc

    analytics = build_analytics_stub(quote)
    return InternalAnalysisResult(quote=quote, analytics=analytics)
