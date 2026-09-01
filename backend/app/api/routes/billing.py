import csv
import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
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


@router.post("/bulk", status_code=201)
def create_billing_records_bulk(payload: list[BillingRecordCreate], db: Session = Depends(get_db)):
    """
    Create many billing records in one request (e.g. after a frontend
    parses a CSV/spreadsheet client-side). Rows with an unknown
    customer_id are skipped and reported back rather than failing
    the whole batch.
    """
    created = []
    errors = []

    for i, row in enumerate(payload):
        if not db.get(Customer, row.customer_id):
            errors.append({"row": i, "customer_id": row.customer_id, "error": "Customer not found"})
            continue
        record = BillingRecord(**row.model_dump())
        db.add(record)
        created.append(record)

    db.commit()
    for record in created:
        db.refresh(record)

    return {
        "created_count": len(created),
        "error_count": len(errors),
        "errors": errors,
    }


@router.post("/upload")
async def upload_billing_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a CSV of billing records directly. Expected columns match
    BillingRecordCreate's fields (e.g. customer_id, amount, period_start,
    period_end, ...). Saves valid rows; invalid/unmatched rows are
    reported back instead of failing the whole file.
    """
    if file.content_type not in ("text/csv", "application/vnd.ms-excel"):
        raise HTTPException(400, "Only CSV files are supported")

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(400, "Could not decode file as UTF-8 CSV")

    reader = csv.DictReader(io.StringIO(text))

    created = []
    errors = []

    for i, row in enumerate(reader):
        try:
            payload = BillingRecordCreate(**row)
        except Exception as e:
            errors.append({"row": i, "error": f"Invalid row: {e}"})
            continue

        if not db.get(Customer, payload.customer_id):
            errors.append({"row": i, "customer_id": payload.customer_id, "error": "Customer not found"})
            continue

        record = BillingRecord(**payload.model_dump())
        db.add(record)
        created.append(record)

    db.commit()
    for record in created:
        db.refresh(record)

    return {
        "created_count": len(created),
        "error_count": len(errors),
        "errors": errors,
    }