"""
The reconciliation engine: deterministic, auditable comparison logic
across Contract <-> Entitlement <-> Usage <-> Billing.

Deliberately NOT an LLM call. An AI model can help *explain* a flagged
discrepancy in plain language (see services/ai_insight.py), but the
decision of whether a discrepancy exists is plain arithmetic against
the ledger -- finance needs to trust every number, and "the model
decided" is not an acceptable answer for a billing dispute.

Each check below returns a list of ReconciliationEvent rows to upsert.
Run this on a schedule (see main.py's /reconciliation/run endpoint,
or wire it to a cron/Celery beat job) against the current period.
"""
from datetime import date
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import (
    Customer,
    Contract,
    ContractLineItem,
    Entitlement,
    UsageRecord,
    BillingRecord,
    ReconciliationEvent,
    DiscrepancyType,
    Severity,
    ReconciliationStatus,
)


def _severity_for(delta_amount: float) -> Severity:
    """Simple $-impact banding. Tune thresholds per business size."""
    if delta_amount >= 15_000:
        return Severity.CRITICAL
    if delta_amount >= 5_000:
        return Severity.HIGH
    if delta_amount >= 1_000:
        return Severity.MEDIUM
    return Severity.LOW


def _active_line_item(contract: Contract, product_sku: str) -> ContractLineItem | None:
    for li in contract.line_items:
        if li.product_sku == product_sku:
            return li
    return None


def _upsert_event(
    db: Session,
    *,
    customer_id: str,
    product_sku: str,
    period_start: date,
    period_end: date,
    discrepancy_type: DiscrepancyType,
    expected_value: float | None,
    actual_value: float | None,
    delta_amount: float,
    explanation: str,
) -> ReconciliationEvent:
    """
    Avoid re-flagging the same open discrepancy every run: look for an
    existing OPEN event for this (customer, sku, period, type) and
    update its numbers instead of duplicating it.
    """
    existing = (
        db.query(ReconciliationEvent)
        .filter_by(
            customer_id=customer_id,
            product_sku=product_sku,
            period_start=period_start,
            period_end=period_end,
            discrepancy_type=discrepancy_type,
            status=ReconciliationStatus.OPEN,
        )
        .first()
    )
    if existing:
        existing.expected_value = expected_value
        existing.actual_value = actual_value
        existing.delta_amount = delta_amount
        existing.explanation = explanation
        existing.severity = _severity_for(delta_amount)
        return existing

    event = ReconciliationEvent(
        customer_id=customer_id,
        product_sku=product_sku,
        period_start=period_start,
        period_end=period_end,
        discrepancy_type=discrepancy_type,
        severity=_severity_for(delta_amount),
        expected_value=expected_value,
        actual_value=actual_value,
        delta_amount=delta_amount,
        status=ReconciliationStatus.OPEN,
        explanation=explanation,
    )
    db.add(event)
    return event


def check_usage_exceeds_entitlement(db: Session, customer: Customer, period_start: date, period_end: date) -> list[ReconciliationEvent]:
    """Usage metered above what the customer is entitled to -> catch-up billing candidate."""
    events = []
    usage_by_sku: dict[str, float] = defaultdict(float)
    for u in customer.usage_records:
        if u.period_start >= period_start and u.period_end <= period_end:
            usage_by_sku[u.product_sku] += u.metered_quantity

    entitlement_by_sku: dict[str, float] = {}
    for e in customer.entitlements:
        if e.granted_quantity is not None:
            entitlement_by_sku[e.product_sku] = e.granted_quantity

    active_contract = next((c for c in customer.contracts if c.status == "active"), None)

    for sku, used in usage_by_sku.items():
        entitled = entitlement_by_sku.get(sku)
        if entitled is None or used <= entitled:
            continue

        overage_units = used - entitled
        rate = None
        line_item = _active_line_item(active_contract, sku) if active_contract else None
        if line_item and line_item.overage_unit_rate:
            rate = line_item.overage_unit_rate
        elif line_item and line_item.unit_price:
            rate = line_item.unit_price  # fall back to list price per unit

        delta = round(overage_units * rate, 2) if rate else 0.0
        if line_item and line_item.overage_cap:
            delta = min(delta, line_item.overage_cap)

        events.append(
            _upsert_event(
                db,
                customer_id=customer.id,
                product_sku=sku,
                period_start=period_start,
                period_end=period_end,
                discrepancy_type=DiscrepancyType.USAGE_EXCEEDS_ENTITLEMENT,
                expected_value=entitled,
                actual_value=used,
                delta_amount=delta,
                explanation=(
                    f"{customer.name} used {used:g} units of {sku} against an entitlement of "
                    f"{entitled:g}. {overage_units:g} unit overage."
                ),
            )
        )
    return events


def check_provisioned_not_billed(db: Session, customer: Customer, period_start: date, period_end: date) -> list[ReconciliationEvent]:
    """Something was granted access (Entitlement) but no matching BillingRecord exists for the period."""
    events = []
    billed_skus = {
        b.product_sku
        for b in customer.billing_records
        if b.period_start >= period_start and b.period_end <= period_end
    }
    active_contract = next((c for c in customer.contracts if c.status == "active"), None)

    for ent in customer.entitlements:
        if ent.product_sku in billed_skus:
            continue
        line_item = _active_line_item(active_contract, ent.product_sku) if active_contract else None
        if not line_item or not line_item.unit_price:
            continue  # can't price it -- surface for manual review elsewhere, don't guess a $ amount

        quantity = ent.granted_quantity or 1
        delta = round(quantity * line_item.unit_price, 2)

        events.append(
            _upsert_event(
                db,
                customer_id=customer.id,
                product_sku=ent.product_sku,
                period_start=period_start,
                period_end=period_end,
                discrepancy_type=DiscrepancyType.PROVISIONED_NOT_BILLED,
                expected_value=quantity,
                actual_value=0,
                delta_amount=delta,
                explanation=(
                    f"{customer.name} was provisioned {quantity:g} units of {ent.product_sku} "
                    f"but no invoice line for this period covers it."
                ),
            )
        )
    return events


def check_expired_discount_still_applied(db: Session, customer: Customer, period_start: date, period_end: date) -> list[ReconciliationEvent]:
    """A contract discount has an expiry date in the past, but billing is still applying it."""
    events = []
    active_contract = next((c for c in customer.contracts if c.status == "active"), None)
    if not active_contract:
        return events

    for record in customer.billing_records:
        if not (record.period_start >= period_start and record.period_end <= period_end):
            continue
        if record.discount_applied_pct <= 0:
            continue

        line_item = _active_line_item(active_contract, record.product_sku)
        if not line_item or not line_item.discount_expiry_date:
            continue
        if line_item.discount_expiry_date >= record.period_start:
            continue  # discount hadn't expired yet for this billing period

        full_amount = record.billed_amount / (1 - record.discount_applied_pct / 100) if record.discount_applied_pct < 100 else record.billed_amount
        delta = round(full_amount - record.billed_amount, 2)

        events.append(
            _upsert_event(
                db,
                customer_id=customer.id,
                product_sku=record.product_sku,
                period_start=period_start,
                period_end=period_end,
                discrepancy_type=DiscrepancyType.EXPIRED_DISCOUNT_STILL_APPLIED,
                expected_value=0,
                actual_value=record.discount_applied_pct,
                delta_amount=delta,
                explanation=(
                    f"A {record.discount_applied_pct:g}% discount on {record.product_sku} expired "
                    f"{line_item.discount_expiry_date.isoformat()} but is still being applied on "
                    f"invoice {record.invoice_id}."
                ),
            )
        )
    return events


def check_entitlement_contract_mismatch(db: Session, customer: Customer, period_start: date, period_end: date) -> list[ReconciliationEvent]:
    """Provisioning drifted from what the contract actually specifies (over- or under-granted)."""
    events = []
    active_contract = next((c for c in customer.contracts if c.status == "active"), None)
    if not active_contract:
        return events

    for ent in customer.entitlements:
        line_item = _active_line_item(active_contract, ent.product_sku)
        if not line_item or line_item.entitled_quantity is None or ent.granted_quantity is None:
            continue
        if ent.granted_quantity == line_item.entitled_quantity:
            continue

        drift = ent.granted_quantity - line_item.entitled_quantity
        rate = line_item.unit_price or 0
        delta = round(abs(drift) * rate, 2)
        if delta == 0:
            continue

        events.append(
            _upsert_event(
                db,
                customer_id=customer.id,
                product_sku=ent.product_sku,
                period_start=period_start,
                period_end=period_end,
                discrepancy_type=DiscrepancyType.ENTITLEMENT_CONTRACT_MISMATCH,
                expected_value=line_item.entitled_quantity,
                actual_value=ent.granted_quantity,
                delta_amount=delta,
                explanation=(
                    f"Contract entitles {customer.name} to {line_item.entitled_quantity:g} units of "
                    f"{ent.product_sku}, but {ent.granted_quantity:g} were provisioned."
                ),
            )
        )
    return events


def run_reconciliation(db: Session, period_start: date, period_end: date) -> list[ReconciliationEvent]:
    """Run all four checks for every customer, then commit."""
    all_events: list[ReconciliationEvent] = []
    for customer in db.query(Customer).all():
        all_events += check_usage_exceeds_entitlement(db, customer, period_start, period_end)
        all_events += check_provisioned_not_billed(db, customer, period_start, period_end)
        all_events += check_expired_discount_still_applied(db, customer, period_start, period_end)
        all_events += check_entitlement_contract_mismatch(db, customer, period_start, period_end)

    db.commit()
    for e in all_events:
        db.refresh(e)
    return all_events
