FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels .


FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    PRICING_PARAMS_PATH=/app/config/pricing_params.yaml \
    LOG_LEVEL=INFO \
    CORS_ALLOWED_ORIGINS=* \
    INTERNAL_API_TOKEN=replace-me

WORKDIR /app

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

COPY config ./config

EXPOSE 8000

CMD ["uvicorn", "ccb.main:app", "--host", "0.0.0.0", "--port", "8000"]

