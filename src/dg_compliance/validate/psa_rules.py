"""PSA Singapore DG Group 1/2/3 classification (sample table)."""

from __future__ import annotations

import json
from functools import lru_cache

from dg_compliance.models.canonical import (
    CanonicalImdgItem,
    Finding,
    FindingSeverity,
    PsaGroup,
)
from dg_compliance.paths import psa_groups_path


@lru_cache(maxsize=1)
def _psa_table() -> dict:
    return json.loads(psa_groups_path().read_text(encoding="utf-8"))


def assign_psa_group(item: CanonicalImdgItem) -> list[Finding]:
    """Set item.psa_group from sample PSA table; warn on Group 1."""
    findings: list[Finding] = []
    if not item.is_dangerous_goods or not item.un_number:
        return findings

    table = _psa_table()
    by_un = table.get("by_un", {})
    entry = by_un.get(item.un_number)
    if entry:
        group = str(entry["group"])
        note = entry.get("note")
    else:
        group = str(table.get("default_group", "3"))
        note = "Default PSA Group 3 (not in sample table)"
        findings.append(
            Finding(
                code="PSA_DEFAULT",
                severity=FindingSeverity.INFO,
                message=note,
                details={"un_number": item.un_number, "group": group},
            )
        )

    item.psa_group = PsaGroup(group)

    if item.psa_group == PsaGroup.GROUP_1:
        findings.append(
            Finding(
                code="PSA_GROUP_1",
                severity=FindingSeverity.WARNING,
                message="PSA Group 1: Direct Delivery only (no yard dwell permitted)",
                details={"un_number": item.un_number, "note": note},
            )
        )
    elif item.psa_group == PsaGroup.GROUP_2:
        findings.append(
            Finding(
                code="PSA_GROUP_2",
                severity=FindingSeverity.INFO,
                message="PSA Group 2: Restricted storage",
                details={"un_number": item.un_number, "note": note},
            )
        )

    return findings
