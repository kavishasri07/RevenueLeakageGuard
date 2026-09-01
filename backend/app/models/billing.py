import uuid
from datetime import date

from sqlalchemy import String, Date, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class BillingRecord(Base):
    __tablename__ = "billing_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    customer_id: Mapped[str] = mapped_column(String, ForeignKey("customers.id"), nullable=False)
    contract_line_item_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("contract_line_items.id"), nullable=True
    )

    invoice_id: Mapped[str] = mapped_column(String, nullable=False)
    product_sku: Mapped[str] = mapped_column(String, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    billed_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    billed_amount: Mapped[float] = mapped_column(Float, nullable=False)
    discount_applied_pct: Mapped[float] = mapped_column(Float, default=0.0)

    customer = relationship("Customer", back_populates="billing_records")
