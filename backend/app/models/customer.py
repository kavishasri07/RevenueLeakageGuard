"""Customer: the anchor entity every other table hangs off of."""
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    account_owner: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    contracts = relationship("Contract", back_populates="customer", cascade="all, delete-orphan")
    entitlements = relationship("Entitlement", back_populates="customer", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="customer", cascade="all, delete-orphan")
    billing_records = relationship("BillingRecord", back_populates="customer", cascade="all, delete-orphan")
    reconciliation_events = relationship("ReconciliationEvent", back_populates="customer", cascade="all, delete-orphan")
