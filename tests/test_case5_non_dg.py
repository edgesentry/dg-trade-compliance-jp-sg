"""Case 5: Non-DG — skip hakushi/akagami/cyberport."""

from dg_compliance.ontology.pipeline import run_ontology
from fixtures import case5_non_dg


def test_case5_non_dg_skips_forms():
    result = run_ontology([case5_non_dg()])
    assert result.export_blocked is False
    assert result.skip_dg_forms is True
    assert result.projections.hakushi_text is None
    assert result.projections.akagami_text is None
    assert result.projections.cyberport is None
    assert result.projections.pan is None
    assert any(f.code == "NOT_REGULATED" for f in result.findings)
    assert result.shipment.items[0].is_dangerous_goods is False
