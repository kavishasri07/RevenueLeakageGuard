"""
App entrypoint. Run with:  uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
import app.models  # noqa: F401 -- import so all tables register on Base

from app.api.routes import customers, contracts, entitlements, usage, billing, reconciliation, reports, ai_analysis

settings = get_settings()

app = FastAPI(
    title="Revenue Leakage Guard API",
    description="Reconciles contracts, entitlements, usage, and billing to catch B2B SaaS revenue leakage.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(customers.router)
app.include_router(contracts.router)
app.include_router(entitlements.router)
app.include_router(usage.router)
app.include_router(billing.router)
app.include_router(reconciliation.router)
app.include_router(reports.router)
app.include_router(ai_analysis.router)
