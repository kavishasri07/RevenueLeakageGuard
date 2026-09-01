import enum
import uuid
from datetime import date, datetime

from sqlalchemy import String, Date, DateTime, Float, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class DiscrepancyType(str, enum.Enum):
    USAGE_EXCEEDS_ENTITLEMENT = "usage_exceeds_entitlement"
    PROVISIONED_NOT_BILLED = "provisioned_not_billed"
    EXPIRED_DISCOUNT_STILL_APPLIED = "expired_discount_still_applied"
    ENTITLEMENT_CONTRACT_MISMATCH = "entitlement_contract_mismatch"


class Severity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReconciliationStatus(str, enum.Enum):
    OPEN = "open"
    PROPOSED = "proposed"              # catch-up billing proposal drafted
    FINANCE_APPROVED = "finance_approved"
    REJECTED = "rejected"
    RESOLVED = "resolved"


class ReconciliationEvent(Base):
    __tablename__ = "reconciliation_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    customer_id: Mapped[str] = mapped_column(String, ForeignKey("customers.id"), nullable=False)

    product_sku: Mapped[str] = mapped_column(String, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    discrepancy_type: Mapped[DiscrepancyType] = mapped_column(Enum(DiscrepancyType), nullable=False)
    severity: Mapped[Severity] = mapped_column(Enum(Severity), default=Severity.MEDIUM)

    expected_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    delta_amount: Mapped[float] = mapped_column(Float, nullable=False)  # $ impact, always positive

    status: Mapped[ReconciliationStatus] = mapped_column(Enum(ReconciliationStatus), default=ReconciliationStatus.OPEN)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)  # human/AI-readable "why"

    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    approved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_invoice_id: Mapped[str | None] = mapped_column(String, nullable=True)

    customer = relationship("Customer", back_populates="reconciliation_events")
