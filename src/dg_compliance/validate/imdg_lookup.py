"""IMDG Dangerous Goods List (sample) lookup and enrichment."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from dg_compliance.models.canonical import CanonicalImdgItem, Finding, FindingSeverity
from dg_compliance.models.extraction import PackingGroup
from dg_compliance.paths import imdg_dgl_path


@lru_cache(maxsize=1)
def _load_dgl() -> dict[str, dict[str, Any]]:
    raw = json.loads(imdg_dgl_path().read_text(encoding="utf-8"))
    return {e["un_number"]: e for e in raw["entries"]}


def enrich_from_dgl(item: CanonicalImdgItem) -> list[Finding]:
    """Match UN against sample DGL; fill gaps; flag mismatches."""
    findings: list[Finding] = []
    if not item.is_dangerous_goods:
        return findings
    if not item.un_number:
        findings.append(
            Finding(
                code="MISSING_UN",
                severity=FindingSeverity.ERROR,
                message="Dangerous goods flagged but UN number is missing",
            )
        )
        return findings

    dgl = _load_dgl()
    entry = dgl.get(item.un_number)
    if entry is None:
        findings.append(
            Finding(
                code="UNKNOWN_UN",
                severity=FindingSeverity.ERROR,
                message=f"{item.un_number} not found in sample IMDG DGL",
                details={"un_number": item.un_number},
            )
        )
        return findings

    item.dgl_matched = True

    if not item.proper_shipping_name:
        item.proper_shipping_name = entry.get("proper_shipping_name")
    elif (
        entry.get("proper_shipping_name")
        and item.proper_shipping_name.upper() != str(entry["proper_shipping_name"]).upper()
    ):
        findings.append(
            Finding(
                code="PSN_MISMATCH",
                severity=FindingSeverity.WARNING,
                message="Extracted PSN differs from DGL sample",
                details={
                    "extracted": item.proper_shipping_name,
                    "dgl": entry["proper_shipping_name"],
                },
            )
        )

    if not item.hazard_class:
        item.hazard_class = entry.get("hazard_class")
    elif entry.get("hazard_class") and item.hazard_class != entry["hazard_class"]:
        findings.append(
            Finding(
                code="CLASS_MISMATCH",
                severity=FindingSeverity.WARNING,
                message="Extracted hazard class differs from DGL sample",
                details={
                    "extracted": item.hazard_class,
                    "dgl": entry["hazard_class"],
                },
            )
        )

    if item.packing_group is None and entry.get("packing_group"):
        item.packing_group = PackingGroup(entry["packing_group"])
    elif (
        item.packing_group is not None
        and entry.get("packing_group")
        and item.packing_group.value != entry["packing_group"]
    ):
        findings.append(
            Finding(
                code="PG_MISMATCH",
                severity=FindingSeverity.WARNING,
                message="Extracted packing group differs from DGL sample",
                details={
                    "extracted": item.packing_group.value,
                    "dgl": entry["packing_group"],
                },
            )
        )

    if item.marine_pollutant is None and "marine_pollutant" in entry:
        item.marine_pollutant = entry["marine_pollutant"]

    return findings
