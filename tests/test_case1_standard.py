"""Case 1: UN1170 Ethanol — hakushi/akagami/cyberport + PSA Group 3."""

from dg_compliance.models.canonical import PsaGroup
from dg_compliance.ontology.pipeline import run_ontology
from fixtures import case1_ethanol


def test_case1_standard_projections_and_psa_group3():
    result = run_ontology([case1_ethanol()], container_id="TESTU1234567")
    assert result.export_blocked is False
    assert result.skip_dg_forms is False
    assert result.projections.hakushi_text is not None
    assert "UN1170" in result.projections.hakushi_text
    assert result.projections.akagami_text is not None
    assert result.projections.cyberport is not None
    assert result.projections.cyberport["dangerousGoods"][0]["unNumber"] == "UN1170"
    assert result.projections.pan is not None
    item = result.shipment.items[0]
    assert item.psa_group == PsaGroup.GROUP_3
    assert item.dgl_matched is True
    assert "PSA_GROUP_3" in result.tags
