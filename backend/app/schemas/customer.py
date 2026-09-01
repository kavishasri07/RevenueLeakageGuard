from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CustomerBase(BaseModel):
    name: str
    account_owner: str | None = None


class CustomerCreate(CustomerBase):
    pass


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
