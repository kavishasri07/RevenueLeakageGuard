"""
UsageRecord: metered product usage, pre-aggregated to a period.
Raw event-level telemetry should be rolled up (daily/monthly) before
it ever reaches this table -- reconciliation runs against aggregates,
not raw events.
"""
import uuid
from datetime import date

from sqlalchemy import String, Date, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    customer_id: Mapped[str] = mapped_column(String, ForeignKey("customers.id"), nullable=False)

    product_sku: Mapped[str] = mapped_column(String, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    metered_quantity: Mapped[float] = mapped_column(Float, nullable=False)  # e.g. active seats, API calls

    customer = relationship("Customer", back_populates="usage_records")
