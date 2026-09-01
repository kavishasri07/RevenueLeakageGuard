from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ReconciliationEvent, ReconciliationStatus
from app.schemas.reconciliation import (
    ReconciliationEventOut,
    ReconciliationApproval,
    ReconciliationRejection,
)
from app.services.reconciliation_engine import run_reconciliation

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


@router.post("/run", response_model=list[ReconciliationEventOut])
def trigger_reconciliation(period_start: date, period_end: date, db: Session = Depends(get_db)):
    """
    Runs all four checks for every customer over the given period.
    In production this is what a scheduled job calls; exposed as an
    endpoint here so it can be triggered on demand for a demo.
    """
    return run_reconciliation(db, period_start, period_end)


@router.get("", response_model=list[ReconciliationEventOut])
def list_events(
    status: ReconciliationStatus | None = None,
    customer_id: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(ReconciliationEvent)
    if status:
        q = q.filter(ReconciliationEvent.status == status)
    if customer_id:
        q = q.filter(ReconciliationEvent.customer_id == customer_id)
    return q.order_by(ReconciliationEvent.delta_amount.desc()).all()


@router.post("/{event_id}/approve", response_model=ReconciliationEventOut)
def approve_event(event_id: str, payload: ReconciliationApproval, db: Session = Depends(get_db)):
    """Finance approves a catch-up billing / correction proposal -- the only path that authorizes a customer-facing change."""
    event = db.get(ReconciliationEvent, event_id)
    if not event:
        raise HTTPException(404, "Reconciliation event not found")

    event.status = ReconciliationStatus.FINANCE_APPROVED
    event.approved_by = payload.approved_by
    event.approved_at = datetime.utcnow()
    event.resolved_invoice_id = payload.resolved_invoice_id
    db.commit()
    db.refresh(event)
    return event


@router.post("/{event_id}/reject", response_model=ReconciliationEventOut)
def reject_event(event_id: str, payload: ReconciliationRejection, db: Session = Depends(get_db)):
    event = db.get(ReconciliationEvent, event_id)
    if not event:
        raise HTTPException(404, "Reconciliation event not found")

    event.status = ReconciliationStatus.REJECTED
    event.explanation = (event.explanation or "") + f"\n\nRejected by {payload.rejected_by}: {payload.reason or 'no reason given'}"
    db.commit()
    db.refresh(event)
    return event
