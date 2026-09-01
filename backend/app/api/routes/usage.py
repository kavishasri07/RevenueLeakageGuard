import csv
import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
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
    """
    Bulk ingest -- the realistic path for product telemetry pipelines.

    Each row's customer_id is validated before insert. A row with an
    unknown customer_id is skipped and reported rather than aborting
    (or silently failing) the whole batch.
    """
    created = []
    errors = []

    for i, payload in enumerate(payloads):
        if not db.get(Customer, payload.customer_id):
            errors.append({"row": i, "customer_id": payload.customer_id, "error": "Customer not found"})
            continue
        record = UsageRecord(**payload.model_dump())
        db.add(record)
        created.append(record)

    db.commit()

    return {
        "created_count": len(created),
        "error_count": len(errors),
        "errors": errors,
    }


@router.post("/upload")
async def upload_usage_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a CSV of usage records directly. Expected columns match
    UsageRecordCreate's fields (e.g. customer_id, metric, quantity,
    recorded_at, ...). Valid rows are saved; invalid/unmatched rows
    are reported back instead of failing the whole file.
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
            payload = UsageRecordCreate(**row)
        except Exception as e:
            errors.append({"row": i, "error": f"Invalid row: {e}"})
            continue

        if not db.get(Customer, payload.customer_id):
            errors.append({"row": i, "customer_id": payload.customer_id, "error": "Customer not found"})
            continue

        record = UsageRecord(**payload.model_dump())
        db.add(record)
        created.append(record)

    db.commit()

    return {
        "created_count": len(created),
        "error_count": len(errors),
        "errors": errors,
    }