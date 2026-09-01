from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ReconciliationEvent, Customer
from app.services.ai_insight import get_leak_insight

router = APIRouter(prefix="/ai-analysis", tags=["ai-analysis"])


@router.get("/insight/{event_id}")
def leak_insight(event_id: str, db: Session = Depends(get_db)):
    """Powers the 'AI Revenue Insight' card -- plain-language explanation of one flagged leak."""
    event = db.get(ReconciliationEvent, event_id)
    if not event:
        raise HTTPException(404, "Reconciliation event not found")
    customer = db.get(Customer, event.customer_id)

    return {"event_id": event.id, "insight": get_leak_insight(event, customer)}
