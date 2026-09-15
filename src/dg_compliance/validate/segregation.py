"""IMDG 7.2.4 segregation — sample forbidden class pairs."""

from __future__ import annotations

import json
from functools import lru_cache

from dg_compliance.models.canonical import CanonicalImdgItem, Finding, FindingSeverity
from dg_compliance.paths import segregation_path


@lru_cache(maxsize=1)
def _forbidden_pairs() -> list[dict]:
    raw = json.loads(segregation_path().read_text(encoding="utf-8"))
    return list(raw["forbidden_class_pairs"])


def _norm(c: str) -> str:
    return c.strip()


def check_segregation(items: list[CanonicalImdgItem]) -> list[Finding]:
    """Return BLOCK findings when co-loaded classes conflict."""
    dg_items = [i for i in items if i.is_dangerous_goods and i.hazard_class]
    findings: list[Finding] = []
    pairs = _forbidden_pairs()

    for i, a in enumerate(dg_items):
        for b in dg_items[i + 1 :]:
            ca, cb = _norm(a.hazard_class or ""), _norm(b.hazard_class or "")
            for rule in pairs:
                ra, rb = _norm(rule["a"]), _norm(rule["b"])
                if {ca, cb} == {ra, rb}:
                    findings.append(
                        Finding(
                            code=rule.get("code", "SEGREGATION_CONFLICT"),
                            severity=FindingSeverity.BLOCK,
                            message=rule.get(
                                "message",
                                f"Segregation conflict between Class {ca} and Class {cb}",
                            ),
                            details={
                                "class_a": ca,
                                "class_b": cb,
                                "un_a": a.un_number,
                                "un_b": b.un_number,
                            },
                        )
                    )
    return findings
