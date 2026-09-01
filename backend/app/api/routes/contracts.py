from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Contract, ContractLineItem, Customer
from app.schemas.contract import ContractCreate, ContractOut
from app.services.contract_extraction import extract_text_from_pdf, extract_contract_terms

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.get("", response_model=list[ContractOut])
def list_contracts(customer_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Contract)
    if customer_id:
        q = q.filter(Contract.customer_id == customer_id)
    return q.all()


@router.post("", response_model=ContractOut, status_code=201)
def create_contract(payload: ContractCreate, db: Session = Depends(get_db)):
    if not db.get(Customer, payload.customer_id):
        raise HTTPException(404, "Customer not found")

    contract = Contract(
        customer_id=payload.customer_id,
        effective_date=payload.effective_date,
        term_end=payload.term_end,
        source_doc_ref=payload.source_doc_ref,
        status=payload.status,
    )
    db.add(contract)
    db.flush()  # get contract.id before adding line items

    for li in payload.line_items:
        db.add(ContractLineItem(contract_id=contract.id, **li.model_dump()))

    db.commit()
    db.refresh(contract)
    return contract


@router.post("/extract")
async def extract_contract(
    file: UploadFile = File(...),
    customer_id: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Upload a contract PDF and get back proposed structured line items.

    - If `customer_id` is NOT provided: line items are returned for
      client-side review only. Nothing is saved. The caller must then
      POST to /contracts with the confirmed line_items to persist them.
    - If `customer_id` IS provided: a draft Contract + line items are
      saved immediately in this single request (upload = save).
    """
    import tempfile, os

    if file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDF files are supported")

    if customer_id and not db.get(Customer, customer_id):
        raise HTTPException(404, "Customer not found")

    suffix = os.path.splitext(file.filename or "contract.pdf")[1] or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        text = extract_text_from_pdf(tmp_path)
        line_items = extract_contract_terms(text)
    except Exception as e:
        raise HTTPException(422, f"Could not extract contract terms: {e}")
    finally:
        os.unlink(tmp_path)

    if not customer_id:
        return {"line_items": line_items, "saved": False}

    contract = Contract(
        customer_id=customer_id,
        source_doc_ref=file.filename,
        status="draft",
    )
    db.add(contract)
    db.flush()  # get contract.id before adding line items

    for li in line_items:
        db.add(ContractLineItem(contract_id=contract.id, **li))

    db.commit()
    db.refresh(contract)

    return {"line_items": line_items, "contract_id": contract.id, "saved": True}


@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(contract_id: str, db: Session = Depends(get_db)):
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(404, "Contract not found")
    return contract