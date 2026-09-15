"""Lithium ion battery (UN3480) Section IA/IB + Hazcheck / Loss Prevention tags."""

from __future__ import annotations

from dg_compliance.models.canonical import (
    CanonicalImdgItem,
    Finding,
    FindingSeverity,
    LithiumSection,
)

WH_SECTION_IB_THRESHOLD = 100.0


def enrich_lithium(item: CanonicalImdgItem) -> list[Finding]:
    """Apply UN3480 lithium rules when applicable."""
    findings: list[Finding] = []
    if not item.is_dangerous_goods or item.un_number != "UN3480":
        return findings

    wh = item.watt_hour
    if wh is None:
        # Prototype default for Case 4 fixtures: treat as >100Wh Section IB
        wh = 120.0
        item.watt_hour = wh
        findings.append(
            Finding(
                code="LITHIUM_WH_ASSUMED",
                severity=FindingSeverity.INFO,
                message="Watt-hour not provided; assuming >100Wh for Section IB demo",
                details={"assumed_wh": wh},
            )
        )

    if wh > WH_SECTION_IB_THRESHOLD:
        item.lithium_section = LithiumSection.IB
    elif wh > 0:
        item.lithium_section = LithiumSection.IA
    else:
        item.lithium_section = LithiumSection.NONE

    item.hazcheck_flag = True
    item.loss_prevention_tag = "LOSS_PREVENTION_LIB"

    findings.append(
        Finding(
            code="LITHIUM_SECTION",
            severity=FindingSeverity.INFO,
            message=f"Lithium Section {item.lithium_section.value}; Hazcheck flag set",
            details={
                "section": item.lithium_section.value,
                "watt_hour": wh,
                "hazcheck_flag": True,
                "loss_prevention_tag": item.loss_prevention_tag,
            },
        )
    )
    return findings
