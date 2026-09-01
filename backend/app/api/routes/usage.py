from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UsageRecord, Customer
from app.schemas.usage import UsageRecordCreate, UsageRecordOut

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("", response_model=list[UsageRecordOut])
def list_usage(customer_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(UsageRecord)
    if customer_id:
        q = q.filter(UsageRecord.customer_id == customer_id)
    return q.all()


@router.post("", response_model=UsageRecordOut, status_code=201)
def record_usage(payload: UsageRecordCreate, db: Session = Depends(get_db)):
    if not db.get(Customer, payload.customer_id):
        raise HTTPException(404, "Customer not found")
    record = UsageRecord(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/bulk", status_code=201)
def record_usage_bulk(payloads: list[UsageRecordCreate], db: Session = Depends(get_db)):
    """Bulk ingest -- this is the realistic path for product telemetry pipelines."""
    records = [UsageRecord(**p.model_dump()) for p in payloads]
    db.add_all(records)
    db.commit()
    return {"created": len(records)}
