"""Case 3: UN3105 organic peroxide — PSA Group 1 warning + JP forms."""

from dg_compliance.models.canonical import FindingSeverity, PsaGroup
from dg_compliance.ontology.pipeline import run_ontology
from fixtures import case3_peroxide


def test_case3_psa_group1_direct_delivery():
    result = run_ontology([case3_peroxide()])
    assert result.export_blocked is False
    assert result.skip_dg_forms is False
    item = result.shipment.items[0]
    assert item.hazard_class == "5.2"
    assert item.psa_group == PsaGroup.GROUP_1
    assert result.projections.hakushi_text is not None
    assert "UN3105" in result.projections.hakushi_text
    warnings = [f for f in result.findings if f.code == "PSA_GROUP_1"]
    assert len(warnings) == 1
    assert warnings[0].severity == FindingSeverity.WARNING
    assert "PSA_GROUP_1" in result.tags
