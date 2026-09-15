"""白紙（危険物明細書）ドラフト — 船社・CY提出用."""

from __future__ import annotations

from dg_compliance.models.canonical import Shipment


def render_hakushi(shipment: Shipment) -> str:
    lines = [
        "危険物明細書（白紙ドラフト）",
        "================================",
        f"コンテナ: {shipment.container_id or '（未指定）'}",
        "",
    ]
    for idx, item in enumerate(shipment.items, start=1):
        if not item.is_dangerous_goods:
            continue
        pg = item.packing_group.value if item.packing_group else "—"
        lines.extend(
            [
                f"--- 品目 {idx} ---",
                f"国連番号: {item.un_number or '—'}",
                f"正式運送品名 (PSN): {item.proper_shipping_name or '—'}",
                f"クラス: {item.hazard_class or '—'}",
                f"副次危険: {item.subsidiary_risk or '—'}",
                f"容器等級: {pg}",
                f"引火点(℃): {item.flash_point_c if item.flash_point_c is not None else '—'}",
                f"海洋汚染物質: {item.marine_pollutant}",
                f"包装: {item.packaging_type or '—'}",
                "",
            ]
        )
    lines.append("Note: 本書類はシステム生成ドラフトです。有資格者が確認後に公式提出してください。")
    return "\n".join(lines)
