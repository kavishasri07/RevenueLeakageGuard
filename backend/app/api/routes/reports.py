"""
Aggregate endpoints that back the dashboard directly -- overview KPIs,
trend chart, category breakdown, and the top-leaks table all map 1:1
to the sections in the frontend mock.
"""
from collections import defaultdict
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ReconciliationEvent, ReconciliationStatus, Customer
from app.schemas.reconciliation import OverviewKPIs, TrendPoint, CategoryBreakdown, TopLeak

router = APIRouter(prefix="/reports", tags=["reports"])

OPEN_STATUSES = (ReconciliationStatus.OPEN, ReconciliationStatus.PROPOSED)


@router.get("/overview", response_model=OverviewKPIs)
def overview_kpis(db: Session = Depends(get_db)):
    open_events = db.query(ReconciliationEvent).filter(ReconciliationEvent.status.in_(OPEN_STATUSES)).all()

    potential_recovery = sum(e.delta_amount for e in open_events)
    active_leaks = len(open_events)
    customers_affected = len({e.customer_id for e in open_events})

    one_week_ago = datetime.utcnow() - timedelta(days=7)
    new_this_week = sum(1 for e in open_events if e.detected_at >= one_week_ago)

    # "Revenue at risk / month" -- normalize usage-exceeds/expired-discount leaks
    # (recurring, ongoing) separately from one-off provisioning misses.
    recurring_types = {"usage_exceeds_entitlement", "expired_discount_still_applied"}
    monthly_at_risk = sum(e.delta_amount for e in open_events if e.discrepancy_type.value in recurring_types)

    one_month_ago = datetime.utcnow() - timedelta(days=30)
    recovery_last_month = sum(e.delta_amount for e in open_events if e.detected_at < one_month_ago)
    pct_change = (
        round((potential_recovery - recovery_last_month) / recovery_last_month * 100, 1)
        if recovery_last_month > 0
        else 0.0
    )

    return OverviewKPIs(
        potential_revenue_recovery=round(potential_recovery, 2),
        recovery_pct_change_mtd=pct_change,
        active_revenue_leaks=active_leaks,
        new_leaks_this_week=new_this_week,
        revenue_at_risk_monthly=round(monthly_at_risk, 2),
        customers_affected=customers_affected,
    )


@router.get("/trend", response_model=list[TrendPoint])
def leakage_trend(months: int = 6, db: Session = Depends(get_db)):
    events = db.query(ReconciliationEvent).all()
    totals: dict[str, float] = defaultdict(float)
    for e in events:
        key = e.detected_at.strftime("%Y-%m")
        totals[key] += e.delta_amount

    points = [TrendPoint(period=k, total_leakage=round(v, 2)) for k, v in sorted(totals.items())]
    return points[-months:]


@router.get("/by-category", response_model=list[CategoryBreakdown])
def leakage_by_category(db: Session = Depends(get_db)):
    open_events = db.query(ReconciliationEvent).filter(ReconciliationEvent.status.in_(OPEN_STATUSES)).all()
    totals: dict = defaultdict(float)
    for e in open_events:
        totals[e.discrepancy_type] += e.delta_amount

    grand_total = sum(totals.values()) or 1  # avoid div-by-zero
    return [
        CategoryBreakdown(
            discrepancy_type=dtype,
            total_amount=round(amount, 2),
            pct_of_total=round(amount / grand_total * 100, 1),
        )
        for dtype, amount in sorted(totals.items(), key=lambda kv: -kv[1])
    ]


@router.get("/top-leaks", response_model=list[TopLeak])
def top_leaks(limit: int = 10, db: Session = Depends(get_db)):
    open_events = (
        db.query(ReconciliationEvent)
        .filter(ReconciliationEvent.status.in_(OPEN_STATUSES))
        .order_by(ReconciliationEvent.delta_amount.desc())
        .limit(limit)
        .all()
    )
    customers = {c.id: c for c in db.query(Customer).all()}

    issue_labels = {
        "usage_exceeds_entitlement": "Usage overage",
        "provisioned_not_billed": "Provisioned, not billed",
        "expired_discount_still_applied": "Expired discount",
        "entitlement_contract_mismatch": "Entitlement drift",
    }

    return [
        TopLeak(
            customer_name=customers[e.customer_id].name if e.customer_id in customers else "Unknown",
            issue=issue_labels.get(e.discrepancy_type.value, e.discrepancy_type.value),
            monthly_impact=e.delta_amount,
            severity=e.severity,
            status=e.status,
            reconciliation_event_id=e.id,
        )
        for e in open_events
    ]
