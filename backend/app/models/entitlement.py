import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Entitlement(Base):
    __tablename__ = "entitlements"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    customer_id: Mapped[str] = mapped_column(String, ForeignKey("customers.id"), nullable=False)
    contract_line_item_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("contract_line_items.id"), nullable=True
    )

    product_sku: Mapped[str] = mapped_column(String, nullable=False)
    granted_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    granted_tier: Mapped[str | None] = mapped_column(String, nullable=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    granted_by: Mapped[str | None] = mapped_column(String, nullable=True)  # ops/CS rep who provisioned it

    customer = relationship("Customer", back_populates="entitlements")
