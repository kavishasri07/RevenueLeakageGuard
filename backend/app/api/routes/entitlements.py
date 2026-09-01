from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Entitlement, Customer
from app.schemas.entitlement import EntitlementCreate, EntitlementOut

router = APIRouter(prefix="/entitlements", tags=["entitlements"])


@router.get("", response_model=list[EntitlementOut])
def list_entitlements(customer_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Entitlement)
    if customer_id:
        q = q.filter(Entitlement.customer_id == customer_id)
    return q.all()


@router.post("", response_model=EntitlementOut, status_code=201)
def create_entitlement(payload: EntitlementCreate, db: Session = Depends(get_db)):
    if not db.get(Customer, payload.customer_id):
        raise HTTPException(404, "Customer not found")
    entitlement = Entitlement(**payload.model_dump())
    db.add(entitlement)
    db.commit()
    db.refresh(entitlement)
    return entitlement
