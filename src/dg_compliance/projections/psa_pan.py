"""digitalPORT@SG Pre-Arrival Notification (PAN) 最小パラメータ."""

from __future__ import annotations

from typing import Any

from dg_compliance.models.canonical import Shipment


def build_pan(shipment: Shipment) -> dict[str, Any]:
    items = []
    for item in shipment.items:
        if not item.is_dangerous_goods:
            continue
        items.append(
            {
                "unNumber": item.un_number,
                "properShippingName": item.proper_shipping_name,
                "imoClass": item.hazard_class,
                "psaDgGroup": item.psa_group.value if item.psa_group else None,
                "lithiumSection": (
                    item.lithium_section.value if item.lithium_section else None
                ),
            }
        )
    return {
        "schema": "digitalport-pan-prototype-v0",
        "etaMinus24hRequired": True,
        "containerId": shipment.container_id,
        "dangerousGoods": items,
        "disclaimer": "Draft only — human submit via digitalPORT@SG; no auto-POST",
    }
