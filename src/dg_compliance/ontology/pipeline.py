"""Ontology Map pipeline: map → validate → project."""

from __future__ import annotations

import json
from pathlib import Path

from dg_compliance.models.canonical import (
    CanonicalImdgItem,
    Finding,
    FindingSeverity,
    OntologyResult,
    ProjectedDocs,
    Shipment,
)
from dg_compliance.models.extraction import ExtractionResult
from dg_compliance.ontology.map import map_extraction
from dg_compliance.projections.akagami import render_akagami
from dg_compliance.projections.cyberport import build_cyberport
from dg_compliance.projections.hakushi import render_hakushi
from dg_compliance.projections.psa_pan import build_pan
from dg_compliance.validate.imdg_lookup import enrich_from_dgl
from dg_compliance.validate.lithium import enrich_lithium
from dg_compliance.validate.psa_rules import assign_psa_group
from dg_compliance.validate.segregation import check_segregation


def run_ontology(
    extractions: list[ExtractionResult],
    *,
    container_id: str | None = None,
    watt_hours: list[float | None] | None = None,
) -> OntologyResult:
    """
    Deterministic Ontology Map for one or more extract results (co-load).

    watt_hours: optional per-item Wh for lithium Case 4.
    """
    items: list[CanonicalImdgItem] = []
    findings: list[Finding] = []

    for i, ext in enumerate(extractions):
        wh = None
        if watt_hours is not None and i < len(watt_hours):
            wh = watt_hours[i]
        item = map_extraction(ext, watt_hour=wh)
        findings.extend(enrich_from_dgl(item))
        findings.extend(assign_psa_group(item))
        findings.extend(enrich_lithium(item))
        items.append(item)

    findings.extend(check_segregation(items))

    shipment = Shipment(items=items, container_id=container_id)
    export_blocked = any(f.severity == FindingSeverity.BLOCK for f in findings)
    all_non_dg = all(not i.is_dangerous_goods for i in items)
    skip_dg_forms = all_non_dg or export_blocked

    if all_non_dg:
        findings.append(
            Finding(
                code="NOT_REGULATED",
                severity=FindingSeverity.INFO,
                message="Not regulated as dangerous goods — DG forms skipped (general cargo)",
            )
        )

    tags: list[str] = []
    for item in items:
        if item.hazcheck_flag:
            tags.append("HAZCHECK")
        if item.loss_prevention_tag:
            tags.append(item.loss_prevention_tag)
        if item.lithium_section and item.lithium_section.value != "NONE":
            tags.append(f"LITHIUM_SECTION_{item.lithium_section.value}")
        if item.psa_group:
            tags.append(f"PSA_GROUP_{item.psa_group.value}")

    projections = ProjectedDocs()
    if not skip_dg_forms:
        projections.hakushi_text = render_hakushi(shipment)
        projections.akagami_text = render_akagami(shipment)
        projections.cyberport = build_cyberport(shipment)
        projections.pan = build_pan(shipment)

    return OntologyResult(
        shipment=shipment,
        findings=findings,
        export_blocked=export_blocked,
        skip_dg_forms=skip_dg_forms,
        projections=projections,
        tags=sorted(set(tags)),
    )


def write_ontology_outputs(result: OntologyResult, output_dir: Path) -> list[Path]:
    """Write ontology_result.json and projection files when not blocked/skipped."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    result_path = output_dir / "ontology_result.json"
    result_path.write_text(
        json.dumps(result.to_pretty_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    written.append(result_path)

    if result.skip_dg_forms:
        return written

    p = result.projections
    if p.hakushi_text:
        path = output_dir / "hakushi.txt"
        path.write_text(p.hakushi_text + "\n", encoding="utf-8")
        written.append(path)
    if p.akagami_text:
        path = output_dir / "akagami.txt"
        path.write_text(p.akagami_text + "\n", encoding="utf-8")
        written.append(path)
    if p.cyberport is not None:
        path = output_dir / "cyberport.json"
        path.write_text(
            json.dumps(p.cyberport, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written.append(path)
    if p.pan is not None:
        path = output_dir / "pan.json"
        path.write_text(
            json.dumps(p.pan, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written.append(path)

    return written
