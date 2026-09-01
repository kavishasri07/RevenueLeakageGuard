"""
Contract term extraction: PDF text -> structured ContractLineItem
fields, via Claude with a strict JSON-only prompt.

Every extracted field keeps its extraction_confidence and
source_clause_ref so a human can verify before anything downstream
(reconciliation, catch-up billing) treats it as ground truth. Low
confidence extractions should be routed to manual review rather than
silently trusted -- do that filtering in the route handler.
"""
import json

from anthropic import Anthropic
from pypdf import PdfReader

from app.config import get_settings

settings = get_settings()
_client: Anthropic | None = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


EXTRACTION_PROMPT = """You extract structured billing terms from SaaS contracts.
Read the contract text below and return ONLY a JSON array (no markdown, no preamble)
of line items, one object per product/SKU, with this exact shape:

[
  {{
    "product_sku": string,
    "entitled_quantity": number or null,
    "entitled_tier": string or null,
    "unit_price": number or null,
    "discount_pct": number,
    "discount_expiry_date": "YYYY-MM-DD" or null,
    "billing_frequency": "monthly" | "annual" | "usage",
    "overage_unit_rate": number or null,
    "overage_cap": number or null,
    "extraction_confidence": number between 0 and 1,
    "source_clause_ref": string (the clause/section you pulled this from, quoted or paraphrased briefly)
  }}
]

Set extraction_confidence below 0.7 for anything ambiguous or inferred rather than stated explicitly.
If a term truly isn't in the contract, use null rather than guessing.

Contract text:
---
{contract_text}
---
"""


def extract_contract_terms(contract_text: str) -> list[dict]:
    """Returns a list of dicts matching ContractLineItemCreate's shape."""
    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(contract_text=contract_text[:50_000])}],
    )
    raw = "".join(block.text for block in response.content if block.type == "text").strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model did not return valid JSON: {exc}\nRaw: {raw[:500]}") from exc
