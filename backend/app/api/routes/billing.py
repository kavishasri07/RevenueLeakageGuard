from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BillingRecord, Customer
from app.schemas.billing import BillingRecordCreate, BillingRecordOut

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("", response_model=list[BillingRecordOut])
def list_billing_records(customer_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(BillingRecord)
    if customer_id:
        q = q.filter(BillingRecord.customer_id == customer_id)
    return q.all()


@router.post("", response_model=BillingRecordOut, status_code=201)
def create_billing_record(payload: BillingRecordCreate, db: Session = Depends(get_db)):
    if not db.get(Customer, payload.customer_id):
        raise HTTPException(404, "Customer not found")
    record = BillingRecord(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
