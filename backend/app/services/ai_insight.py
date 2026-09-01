"""
AI-assisted layer for two narrow use cases:
- Summarizing reconciliation events for Finance.
- Extracting structured terms from contracts.

The LLM is explanatory/extractive only. Financial reconciliation and
decision-making remain deterministic in reconciliation_engine.py.
"""

import json

from anthropic import Anthropic

from app.config import get_settings
from app.models import ReconciliationEvent, Customer

settings = get_settings()
_client: Anthropic | None = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


def summarize_leak(event: ReconciliationEvent, customer: Customer) -> str:
    """
    Produce a 2-3 sentence, finance-readable explanation of a single
    reconciliation event plus a recoverable-revenue estimate --
    mirrors the "AI Revenue Insight" card on the dashboard mock.
    """
    prompt = f"""You are helping a finance team understand a billing discrepancy.
Write a plain, factual, 2-3 sentence summary, followed by a line
"Estimated recoverable revenue: $X/month". No preamble, no markdown.

Discrepancy data:
- Customer: {customer.name}
- Product/SKU: {event.product_sku}
- Type: {event.discrepancy_type.value}
- Expected value: {event.expected_value}
- Actual value: {event.actual_value}
- Dollar impact: ${event.delta_amount:,.2f}
- Period: {event.period_start} to {event.period_end}
"""
    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()


def summarize_leak_fallback(event: ReconciliationEvent, customer: Customer) -> str:
    """
    Deterministic, no-API-key-required fallback so the dashboard still
    works without an Anthropic key configured (e.g. local dev / demo).
    """
    return (
        f"{customer.name} shows a {event.discrepancy_type.value.replace('_', ' ')} "
        f"on {event.product_sku}: expected {event.expected_value}, actual {event.actual_value}.\n"
        f"Estimated recoverable revenue: ${event.delta_amount:,.2f}/month"
    )


def get_leak_insight(event: ReconciliationEvent, customer: Customer) -> str:
    if not settings.anthropic_api_key:
        return summarize_leak_fallback(event, customer)
    try:
        return summarize_leak(event, customer)
    except Exception:
        # Never let a flaky API call break the dashboard -- degrade gracefully.
        return summarize_leak_fallback(event, customer)
