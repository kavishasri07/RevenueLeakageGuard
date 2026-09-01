from datetime import date
from pydantic import BaseModel, ConfigDict


class BillingRecordBase(BaseModel):
    customer_id: str
    contract_line_item_id: str | None = None
    invoice_id: str
    product_sku: str
    period_start: date
    period_end: date
    billed_quantity: float | None = None
    billed_amount: float
    discount_applied_pct: float = 0.0


class BillingRecordCreate(BillingRecordBase):
    pass


class BillingRecordOut(BillingRecordBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
