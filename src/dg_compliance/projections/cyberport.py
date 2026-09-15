"""CyberPort 港湾物流投入用 JSON（プロトタイプ項目セット）."""

from __future__ import annotations

from typing import Any

from dg_compliance.models.canonical import Shipment


def build_cyberport(shipment: Shipment) -> dict[str, Any]:
    goods = []
    for item in shipment.items:
        if not item.is_dangerous_goods:
            continue
        goods.append(
            {
                "unNumber": item.un_number,
                "properShippingName": item.proper_shipping_name,
                "imoClass": item.hazard_class,
                "subsidiaryRisk": item.subsidiary_risk,
                "packingGroup": item.packing_group.value if item.packing_group else None,
                "flashPointC": item.flash_point_c,
                "marinePollutant": item.marine_pollutant,
                "packagingType": item.packaging_type,
            }
        )
    return {
        "schema": "cyberport-dg-prototype-v0",
        "containerId": shipment.container_id,
        "dangerousGoods": goods,
        "disclaimer": "Draft only — human submit via CyberPort portal; no auto-POST",
    }
