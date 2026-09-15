"""Schema / parse helpers — no live LLM required."""

from __future__ import annotations

import json

from dg_compliance.extract.litellm_extractor import (
    DEFAULT_MODEL,
    _parse_payload,
    resolve_model,
)
from dg_compliance.models.extraction import ExtractedDgFields, ExtractionResult


def test_normalize_un_number():
    f = ExtractedDgFields(un_number="1170")
    assert f.un_number == "UN1170"
    f2 = ExtractedDgFields(un_number="un 1170")
    assert f2.un_number == "UN1170"


def test_parse_payload_with_fences():
    raw = """```json
{"fields": {"un_number": "UN1170", "proper_shipping_name": "ETHANOL SOLUTION",
 "hazard_class": "3", "subsidiary_risk": null, "packing_group": "II",
 "flash_point_c": 13, "marine_pollutant": false, "packaging_type": "drum",
 "is_dangerous_goods": true, "language_detected": "en"},
 "evidence": [{"field": "un_number", "page_no": 1, "snippet": "UN 1170"}]}
```"""
    data = _parse_payload(raw)
    fields = ExtractedDgFields.model_validate(data["fields"])
    assert fields.un_number == "UN1170"
    assert fields.flash_point_c == 13


def test_extraction_result_roundtrip():
    result = ExtractionResult(
        source_path="data/samples/sds_un1170_ethanol.txt",
        model=DEFAULT_MODEL,
        fields=ExtractedDgFields(
            un_number="UN1170",
            proper_shipping_name="ETHANOL SOLUTION",
            hazard_class="3",
            packing_group="II",
            flash_point_c=13.0,
            is_dangerous_goods=True,
        ),
        evidence=[],
    )
    dumped = json.loads(json.dumps(result.to_pretty_dict()))
    assert dumped["fields"]["un_number"] == "UN1170"


def test_resolve_model_default(monkeypatch):
    monkeypatch.delenv("DG_EXTRACT_MODEL", raising=False)
    monkeypatch.delenv("LITELLM_MODEL", raising=False)
    assert resolve_model(None) == "gemini/gemini-3.8-flash"
    assert resolve_model("openai/gpt-4o") == "openai/gpt-4o"
    assert resolve_model("anthropic/claude-sonnet-4-20250514") == (
        "anthropic/claude-sonnet-4-20250514"
    )


def test_gemini3_plus_detection():
    from dg_compliance.extract.litellm_extractor import _is_gemini3_plus

    assert _is_gemini3_plus("gemini/gemini-3.8-flash") is True
    assert _is_gemini3_plus("gemini-3.8-flash") is True
    assert _is_gemini3_plus("openai/gpt-4o") is False
    assert _is_gemini3_plus("gemini/gemini-2.0-flash") is False
