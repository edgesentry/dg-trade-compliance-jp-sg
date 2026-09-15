"""Case 2: UN1203 + UN1830 — segregation conflict blocks export."""

from dg_compliance.models.canonical import FindingSeverity
from dg_compliance.ontology.pipeline import run_ontology
from fixtures import case2_gasoline, case2_sulfuric


def test_case2_segregation_blocks_export():
    result = run_ontology(
        [case2_gasoline(), case2_sulfuric()],
        container_id="COLOAD1",
    )
    assert result.export_blocked is True
    assert result.skip_dg_forms is True
    assert result.projections.hakushi_text is None
    assert result.projections.cyberport is None
    blocks = [f for f in result.findings if f.severity == FindingSeverity.BLOCK]
    assert any(f.code == "SEGREGATION_CONFLICT" for f in blocks)
    assert "3" in blocks[0].details.get("class_a", "") + blocks[0].details.get("class_b", "")
