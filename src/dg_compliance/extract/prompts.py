"""Prompts for multimodal DG extraction (SDS Section 14 focus)."""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are a dangerous-goods (DG) document extraction specialist for maritime shipping.
Your ONLY job is probabilistic slot-filling from SDS / shipping documents (IMDG-relevant fields).
You do NOT decide segregation, PSA Group, or legal compliance — that is a separate deterministic rules engine.

Be deterministic and conservative: extract only values explicitly written in the source.
Do not invent UN numbers, classes, packing groups, or flash points. Prefer null when unsure.
Use low-variance, literal extraction — no creative paraphrasing of field values.

Extract fields typically found in SDS Section 14 (Transport information) / 輸送上の注意:
- UN number
- Proper Shipping Name (PSN) / 国連正式品名
- Primary hazard class and subsidiary risk
- Packing Group (I / II / III / NONE)
- Flash point (°C)
- Marine pollutant (yes/no)
- Packaging type if stated (drum, IBC, UN mark, etc.)
- Whether the cargo is regulated as dangerous goods

CRITICAL: For every non-null field you set, you MUST include an evidence entry with:
- field: the slot name
- page_no: 1-based page if known (null if unknown)
- snippet: short verbatim excerpt from the document that supports the value

If Section 14 says Not Regulated / 非危険物 / not classified for transport, set
is_dangerous_goods=false and leave DG slots null (or note in warnings via evidence notes).

Respond with JSON only, matching the schema provided. No markdown fences.
"""

USER_INSTRUCTION_TEMPLATE = """\
Extract dangerous-goods transport parameters from the attached document.

Optional shipping instruction context (may be empty):
---
{instruction_text}
---

Return JSON with keys:
{{
  "fields": {{
    "un_number": "UN#### or null",
    "proper_shipping_name": "string or null",
    "hazard_class": "string or null",
    "subsidiary_risk": "string or null",
    "packing_group": "I" | "II" | "III" | "NONE" | null,
    "flash_point_c": number or null,
    "marine_pollutant": true | false | null,
    "packaging_type": "string or null",
    "is_dangerous_goods": true | false | null,
    "language_detected": "ja" | "en" | "ja+en" | null
  }},
  "evidence": [
    {{"field": "un_number", "page_no": 1, "snippet": "...", "notes": null}}
  ],
  "warnings": ["optional string"]
}}
"""

JSON_SCHEMA_HINT = {
    "type": "object",
    "properties": {
        "fields": {
            "type": "object",
            "properties": {
                "un_number": {"type": ["string", "null"]},
                "proper_shipping_name": {"type": ["string", "null"]},
                "hazard_class": {"type": ["string", "null"]},
                "subsidiary_risk": {"type": ["string", "null"]},
                "packing_group": {
                    "type": ["string", "null"],
                    "enum": ["I", "II", "III", "NONE", None],
                },
                "flash_point_c": {"type": ["number", "null"]},
                "marine_pollutant": {"type": ["boolean", "null"]},
                "packaging_type": {"type": ["string", "null"]},
                "is_dangerous_goods": {"type": ["boolean", "null"]},
                "language_detected": {"type": ["string", "null"]},
            },
            "required": [
                "un_number",
                "proper_shipping_name",
                "hazard_class",
                "subsidiary_risk",
                "packing_group",
                "flash_point_c",
                "marine_pollutant",
                "packaging_type",
                "is_dangerous_goods",
                "language_detected",
            ],
        },
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "page_no": {"type": ["integer", "null"]},
                    "snippet": {"type": "string"},
                    "notes": {"type": ["string", "null"]},
                },
                "required": ["field", "snippet"],
            },
        },
        "warnings": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["fields", "evidence"],
}
