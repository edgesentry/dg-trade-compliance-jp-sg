"""Case 4: UN3480 Li-ion — Section IB, Hazcheck, Loss Prevention tag."""

from dg_compliance.models.canonical import LithiumSection, PsaGroup
from dg_compliance.ontology.pipeline import run_ontology
from fixtures import case4_battery


def test_case4_lithium_section_ib_and_tags():
    result = run_ontology([case4_battery()], watt_hours=[120.0])
    assert result.export_blocked is False
    item = result.shipment.items[0]
    assert item.un_number == "UN3480"
    assert item.lithium_section == LithiumSection.IB
    assert item.hazcheck_flag is True
    assert item.loss_prevention_tag == "LOSS_PREVENTION_LIB"
    assert item.psa_group == PsaGroup.GROUP_2
    assert "HAZCHECK" in result.tags
    assert "LITHIUM_SECTION_IB" in result.tags
    assert "LOSS_PREVENTION_LIB" in result.tags
    assert result.projections.pan is not None
    assert result.projections.pan["dangerousGoods"][0]["lithiumSection"] == "IB"
