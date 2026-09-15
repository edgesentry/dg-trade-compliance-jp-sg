"""Helpers to build ExtractionResult fixtures for Ontology Map tests."""

from __future__ import annotations

from dg_compliance.models.extraction import (
    EvidenceCitation,
    ExtractedDgFields,
    ExtractionResult,
    PackingGroup,
)


def make_extract(
    *,
    un_number: str | None,
    psn: str | None,
    hazard_class: str | None,
    packing_group: PackingGroup | str | None = None,
    flash_point_c: float | None = None,
    is_dangerous_goods: bool = True,
    packaging_type: str | None = None,
    marine_pollutant: bool | None = False,
    source_path: str = "fixture",
) -> ExtractionResult:
    pg = packing_group
    if isinstance(pg, str):
        pg = PackingGroup(pg)
    return ExtractionResult(
        source_path=source_path,
        model="fixture",
        fields=ExtractedDgFields(
            un_number=un_number,
            proper_shipping_name=psn,
            hazard_class=hazard_class,
            packing_group=pg,
            flash_point_c=flash_point_c,
            marine_pollutant=marine_pollutant,
            packaging_type=packaging_type,
            is_dangerous_goods=is_dangerous_goods,
            language_detected="en",
        ),
        evidence=[
            EvidenceCitation(
                field="un_number",
                page_no=1,
                snippet=un_number or "Not regulated",
            )
        ],
    )


def case1_ethanol() -> ExtractionResult:
    return make_extract(
        un_number="UN1170",
        psn="ETHANOL SOLUTION",
        hazard_class="3",
        packing_group="II",
        flash_point_c=13.0,
        packaging_type="Steel drum (UN 1A1), 160 L",
        source_path="data/samples/sds_un1170_ethanol.txt",
    )


def case2_gasoline() -> ExtractionResult:
    return make_extract(
        un_number="UN1203",
        psn="GASOLINE",
        hazard_class="3",
        packing_group="II",
        flash_point_c=-40.0,
        source_path="data/samples/sds_un1203_gasoline.txt",
    )


def case2_sulfuric() -> ExtractionResult:
    return make_extract(
        un_number="UN1830",
        psn="SULPHURIC ACID",
        hazard_class="8",
        packing_group="II",
        source_path="data/samples/sds_un1830_sulfuric_acid.txt",
    )


def case3_peroxide() -> ExtractionResult:
    return make_extract(
        un_number="UN3105",
        psn="ORGANIC PEROXIDE TYPE D, LIQUID",
        hazard_class="5.2",
        packing_group="NONE",
        source_path="data/samples/sds_un3105_peroxide.txt",
    )


def case4_battery() -> ExtractionResult:
    return make_extract(
        un_number="UN3480",
        psn="LITHIUM ION BATTERIES",
        hazard_class="9",
        packing_group="NONE",
        source_path="data/samples/sds_un3480_battery.txt",
    )


def case5_non_dg() -> ExtractionResult:
    return make_extract(
        un_number=None,
        psn=None,
        hazard_class=None,
        packing_group=None,
        is_dangerous_goods=False,
        source_path="data/samples/sds_non_dg_lubricant.txt",
    )
