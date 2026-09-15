"""赤紙（危険物申告書）ドラフト — SK/NKKK コンテナ収納検査用."""

from __future__ import annotations

from dg_compliance.models.canonical import Shipment


def render_akagami(shipment: Shipment) -> str:
    lines = [
        "危険物申告書（赤紙ドラフト）",
        "指定検査機関提出用（SK / NKKK 等）",
        "================================",
        f"コンテナ: {shipment.container_id or '（未指定）'}",
        "",
    ]
    for idx, item in enumerate(shipment.items, start=1):
        if not item.is_dangerous_goods:
            continue
        pg = item.packing_group.value if item.packing_group else "—"
        psa = item.psa_group.value if item.psa_group else "—"
        lines.extend(
            [
                f"--- 品目 {idx} ---",
                f"UN No.: {item.un_number or '—'}",
                f"Proper Shipping Name: {item.proper_shipping_name or '—'}",
                f"Class / Div.: {item.hazard_class or '—'}",
                f"Subsidiary risk: {item.subsidiary_risk or '—'}",
                f"Packing Group: {pg}",
                f"Flash point: {item.flash_point_c if item.flash_point_c is not None else '—'} °C",
                f"Marine pollutant: {item.marine_pollutant}",
                f"Packaging: {item.packaging_type or '—'}",
                f"PSA DG Group (ref): {psa}",
                "",
            ]
        )
    lines.append("Note: 収納検査は検査機関の確認が必須です。自動送信は行いません。")
    return "\n".join(lines)
