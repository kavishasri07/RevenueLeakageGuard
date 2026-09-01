from datetime import datetime
from pydantic import BaseModel, ConfigDict


class EntitlementBase(BaseModel):
    customer_id: str
    contract_line_item_id: str | None = None
    product_sku: str
    granted_quantity: float | None = None
    granted_tier: str | None = None
    granted_by: str | None = None


class EntitlementCreate(EntitlementBase):
    pass


class EntitlementOut(EntitlementBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    granted_at: datetime
