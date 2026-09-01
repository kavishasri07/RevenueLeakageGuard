"""
Import every model here so Base.metadata.create_all() (in main.py)
discovers all tables -- SQLAlchemy only registers a model once its
module has been imported somewhere.
"""
from app.models.customer import Customer
from app.models.contract import Contract, ContractLineItem
from app.models.entitlement import Entitlement
from app.models.usage import UsageRecord
from app.models.billing import BillingRecord
from app.models.reconciliation import (
    ReconciliationEvent,
    DiscrepancyType,
    Severity,
    ReconciliationStatus,
)

__all__ = [
    "Customer",
    "Contract",
    "ContractLineItem",
    "Entitlement",
    "UsageRecord",
    "BillingRecord",
    "ReconciliationEvent",
    "DiscrepancyType",
    "Severity",
    "ReconciliationStatus",
]
