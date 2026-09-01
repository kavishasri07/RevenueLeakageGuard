from datetime import date
from pydantic import BaseModel, ConfigDict


class ContractLineItemBase(BaseModel):
    product_sku: str
    entitled_quantity: float | None = None
    entitled_tier: str | None = None
    unit_price: float | None = None
    discount_pct: float = 0.0
    discount_expiry_date: date | None = None
    billing_frequency: str = "monthly"
    overage_unit_rate: float | None = None
    overage_cap: float | None = None
    extraction_confidence: float = 1.0
    source_clause_ref: str | None = None


class ContractLineItemCreate(ContractLineItemBase):
    pass


class ContractLineItemOut(ContractLineItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    contract_id: str


class ContractBase(BaseModel):
    customer_id: str
    effective_date: date
    term_end: date | None = None
    source_doc_ref: str | None = None
    status: str = "active"


class ContractCreate(ContractBase):
    line_items: list[ContractLineItemCreate] = []


class ContractOut(ContractBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    line_items: list[ContractLineItemOut] = []
