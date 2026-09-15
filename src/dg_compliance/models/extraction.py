"""Layer-1 extraction schemas (probabilistic slots + evidence)."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class PackingGroup(str, Enum):
    I = "I"
    II = "II"
    III = "III"
    NONE = "NONE"  # not assigned / not applicable


class EvidenceCitation(BaseModel):
    """HITL / audit: which page & text grounded a slot."""

    field: str = Field(description="Slot name this evidence supports, e.g. un_number")
    page_no: int | None = Field(
        default=None,
        description="1-based page number in the source PDF/text; null if unknown",
    )
    snippet: str = Field(
        description="Verbatim or near-verbatim excerpt from the source used as evidence"
    )
    notes: str | None = Field(default=None, description="Optional OCR/layout notes")


class ExtractedDgFields(BaseModel):
    """Dangerous-goods parameters from SDS Section 14 / shipping docs."""

    un_number: str | None = Field(
        default=None,
        description="UN number as UN#### (e.g. UN1170); null if not regulated / missing",
    )
    proper_shipping_name: str | None = Field(
        default=None, description="Proper Shipping Name (PSN)"
    )
    hazard_class: str | None = Field(
        default=None, description="Primary IMDG class, e.g. '3' or '5.2'"
    )
    subsidiary_risk: str | None = Field(
        default=None, description="Subsidiary risk class if any"
    )
    packing_group: PackingGroup | None = Field(default=None)
    flash_point_c: float | None = Field(
        default=None, description="Flash point in Celsius"
    )
    marine_pollutant: bool | None = Field(default=None)
    packaging_type: str | None = Field(
        default=None,
        description="Container/packaging description (drum, IBC, UN packaging mark, etc.)",
    )
    is_dangerous_goods: bool | None = Field(
        default=None,
        description="False when Section 14 / transport info says not regulated",
    )
    language_detected: str | None = Field(
        default=None, description="e.g. ja, en, ja+en"
    )

    @field_validator("un_number", mode="before")
    @classmethod
    def normalize_un(cls, v: Any) -> str | None:
        if v is None or v == "":
            return None
        s = str(v).strip().upper().replace(" ", "")
        if s.isdigit():
            s = f"UN{s}"
        if s.startswith("UN") and not s[2:].isdigit() and len(s) > 2:
            # keep as-is; ontology / rule engine will validate later
            return s
        return s


class ExtractionResult(BaseModel):
    """Full Layer-1 output: slots + evidence + model metadata."""

    source_path: str
    model: str
    fields: ExtractedDgFields
    evidence: list[EvidenceCitation] = Field(default_factory=list)
    raw_model_text: str | None = Field(
        default=None, description="Raw LLM response text (debug / audit)"
    )
    warnings: list[str] = Field(default_factory=list)

    def to_pretty_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
