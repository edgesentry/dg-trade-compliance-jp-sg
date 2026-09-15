"""Map ExtractionResult → CanonicalImdgItem (normalize only; no PSA/segregation)."""

from __future__ import annotations

from dg_compliance.models.canonical import CanonicalImdgItem
from dg_compliance.models.extraction import ExtractionResult, PackingGroup


def _normalize_class(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    return str(value).strip()


def map_extraction(
    result: ExtractionResult,
    *,
    watt_hour: float | None = None,
) -> CanonicalImdgItem:
    """Convert probabilistic extract slots into a canonical IMDG item."""
    f = result.fields
    is_dg = f.is_dangerous_goods
    if is_dg is None:
        is_dg = bool(f.un_number)

    pg = f.packing_group
    if isinstance(pg, str):
        pg = PackingGroup(pg)

    return CanonicalImdgItem(
        un_number=f.un_number,
        proper_shipping_name=f.proper_shipping_name,
        hazard_class=_normalize_class(f.hazard_class),
        subsidiary_risk=_normalize_class(f.subsidiary_risk),
        packing_group=pg,
        flash_point_c=f.flash_point_c,
        marine_pollutant=f.marine_pollutant,
        packaging_type=f.packaging_type,
        is_dangerous_goods=bool(is_dg),
        watt_hour=watt_hour,
        source_path=result.source_path,
        evidence=list(result.evidence),
    )
