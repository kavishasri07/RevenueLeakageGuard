from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

from app.models.reconciliation import DiscrepancyType, Severity, ReconciliationStatus


class ReconciliationEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    product_sku: str
    period_start: date
    period_end: date
    discrepancy_type: DiscrepancyType
    severity: Severity
    expected_value: float | None
    actual_value: float | None
    delta_amount: float
    status: ReconciliationStatus
    explanation: str | None
    detected_at: datetime
    approved_by: str | None
    approved_at: datetime | None
    resolved_invoice_id: str | None


class ReconciliationApproval(BaseModel):
    approved_by: str
    resolved_invoice_id: str | None = None


class ReconciliationRejection(BaseModel):
    rejected_by: str
    reason: str | None = None


class OverviewKPIs(BaseModel):
    potential_revenue_recovery: float
    recovery_pct_change_mtd: float
    active_revenue_leaks: int
    new_leaks_this_week: int
    revenue_at_risk_monthly: float
    customers_affected: int


class TrendPoint(BaseModel):
    period: str  # e.g. "2026-01"
    total_leakage: float


class CategoryBreakdown(BaseModel):
    discrepancy_type: DiscrepancyType
    total_amount: float
    pct_of_total: float


class TopLeak(BaseModel):
    customer_name: str
    issue: str
    monthly_impact: float
    severity: Severity
    status: ReconciliationStatus
    reconciliation_event_id: str
