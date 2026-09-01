import uuid
from datetime import date, datetime

from sqlalchemy import String, Date, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    customer_id: Mapped[str] = mapped_column(String, ForeignKey("customers.id"), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    term_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_doc_ref: Mapped[str | None] = mapped_column(String, nullable=True)  # path/URL to the uploaded PDF
    status: Mapped[str] = mapped_column(String, default="active")  # active | superseded | expired
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="contracts")
    line_items = relationship("ContractLineItem", back_populates="contract", cascade="all, delete-orphan")


class ContractLineItem(Base):
    __tablename__ = "contract_line_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    contract_id: Mapped[str] = mapped_column(String, ForeignKey("contracts.id"), nullable=False)

    product_sku: Mapped[str] = mapped_column(String, nullable=False)
    entitled_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)  # e.g. seat count
    entitled_tier: Mapped[str | None] = mapped_column(String, nullable=True)       # e.g. "enterprise"
    unit_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    discount_pct: Mapped[float] = mapped_column(Float, default=0.0)
    discount_expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    billing_frequency: Mapped[str] = mapped_column(String, default="monthly")  # monthly | annual | usage
    overage_unit_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    overage_cap: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Provenance / trust fields -- every derived figure must be traceable
    extraction_confidence: Mapped[float] = mapped_column(Float, default=1.0)  # 0-1, 1.0 = manually entered
    source_clause_ref: Mapped[str | None] = mapped_column(Text, nullable=True)  # page/clause quoted for audit

    contract = relationship("Contract", back_populates="line_items")
