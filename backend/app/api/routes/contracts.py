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
async def extract_contract(file: UploadFile = File(...)):
    """
    Upload a contract PDF, get back proposed structured line items
    (NOT yet saved). Review/edit client-side, then POST to /contracts
    with the confirmed line_items to persist them.
    """
    import tempfile, os

    suffix = os.path.splitext(file.filename or "contract.pdf")[1] or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        text = extract_text_from_pdf(tmp_path)
        line_items = extract_contract_terms(text)
    finally:
        os.unlink(tmp_path)

    return {"line_items": line_items}


@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(contract_id: str, db: Session = Depends(get_db)):
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(404, "Contract not found")
    return contract
