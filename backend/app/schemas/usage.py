from datetime import date
from pydantic import BaseModel, ConfigDict


class UsageRecordBase(BaseModel):
    customer_id: str
    product_sku: str
    period_start: date
    period_end: date
    metered_quantity: float


class UsageRecordCreate(UsageRecordBase):
    pass


class UsageRecordOut(UsageRecordBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
