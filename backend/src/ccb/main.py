from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ccb.api.health import router as health_router
from ccb.api.internal import router as internal_router
from ccb.api.public import router as public_router
from ccb.settings import settings

app = FastAPI(title="CCB Portal API", version="0.1.0")
cors_allowed_origins = (
    ["*"]
    if settings.cors_allowed_origins == "*"
    else settings.cors_allowed_origins.split(",")
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(internal_router)
app.include_router(public_router)
