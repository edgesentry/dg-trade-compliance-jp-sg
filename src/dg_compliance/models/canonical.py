"""Canonical IMDG models + Ontology Map result (deterministic)."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from dg_compliance.models.extraction import EvidenceCitation, PackingGroup


class FindingSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCK = "block"


class Finding(BaseModel):
    code: str
    severity: FindingSeverity
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class PsaGroup(str, Enum):
    GROUP_1 = "1"  # Direct delivery / no yard dwell
    GROUP_2 = "2"  # Restricted storage
    GROUP_3 = "3"  # General storage


class LithiumSection(str, Enum):
    IA = "IA"
    IB = "IB"
    II = "II"
    NONE = "NONE"


class CanonicalImdgItem(BaseModel):
    """IMDG-oriented intermediate representation after extract normalization."""

    un_number: str | None = None
    proper_shipping_name: str | None = None
    hazard_class: str | None = None
    subsidiary_risk: str | None = None
    packing_group: PackingGroup | None = None
    flash_point_c: float | None = None
    marine_pollutant: bool | None = None
    packaging_type: str | None = None
    is_dangerous_goods: bool = False
    watt_hour: float | None = Field(
        default=None, description="Li-ion Wh rating when applicable (UN3480 etc.)"
    )
    source_path: str | None = None
    evidence: list[EvidenceCitation] = Field(default_factory=list)

    # Enriched by validate/
    psa_group: PsaGroup | None = None
    lithium_section: LithiumSection | None = None
    hazcheck_flag: bool = False
    loss_prevention_tag: str | None = None
    dgl_matched: bool = False


class Shipment(BaseModel):
    """One or more DG items in a single container / co-load context."""

    items: list[CanonicalImdgItem]
    container_id: str | None = None


class ProjectedDocs(BaseModel):
    hakushi_text: str | None = None
    akagami_text: str | None = None
    cyberport: dict[str, Any] | None = None
    pan: dict[str, Any] | None = None


class OntologyResult(BaseModel):
    shipment: Shipment
    findings: list[Finding] = Field(default_factory=list)
    export_blocked: bool = False
    skip_dg_forms: bool = False
    projections: ProjectedDocs = Field(default_factory=ProjectedDocs)
    tags: list[str] = Field(default_factory=list)

    def to_pretty_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
