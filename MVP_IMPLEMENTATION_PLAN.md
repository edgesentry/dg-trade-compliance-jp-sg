# MVP Implementation Plan — DG Trade Compliance JP–SG

**Repo:** `dg-trade-compliance-jp-sg`  
**Strategy parents:** `edgesentry-commercial/docs/strategy/dg-trade-compliance-jp-sg/`  
(`mvp.md` · `prototype-plan.md` · `why-input-digitization-vs-insurance.md`)

---

## Principles (must remain visible in code)

1. **Neuro-Symbolic split** — Multimodal Extract (LLM) is probabilistic; Ontology / rules (IMDG · segregation · PSA) are deterministic.
2. **Single canonical → dual jurisdiction** — Japan (白紙/赤紙/CyberPort) and Singapore (PSA Group / PAN).
3. **SHA-256 WORM envelope** — hash input + extract + verify + reviewer token (engine reuse from edgesentry-rs later).
4. **Responsible HITL** — no auto-POST to government APIs (通関業法 3・34).
5. **Headless CLI first** — no mandatory new field GUI.

> Naming: do **not** use `layer1` / `layer2` in file or folder names. Prefer `extract/`, `validate/`, `projections/`.

---

## Milestone progress

| Step | Scope | Status |
|------|--------|--------|
| **Theme 1** | Multimodal Extract via **LiteLLM** (Gemini / OpenAI / Anthropic), evidence page+snippet | **Done** |
| **Theme 2** | Ontology Map + projections + Case 1–5 offline tests | **Done** |
| Theme 3 | HITL preview + export-only | Later |
| Demo suite | Live extract → map demo polish | Next |

**Default extract model:** `gemini/gemini-3.8-flash`

---

## Theme 1 — Extract

- Entry: `uv run dg-compliance extract <sds.pdf|txt|image>`
- Package: `src/dg_compliance/extract/`
- Extract **must not** emit PSA Group or segregation verdicts.

---

## Theme 2 — Ontology Map

```text
ExtractionResult
    → CanonicalImdgItem          (ontology/map.py)
    → DGL enrich + PSA + lithium + segregation  (validate/)
    → hakushi / akagami / cyberport / pan       (projections/)
```

- Entry: `uv run dg-compliance map <extract.json> [--co-load ...] -o dist/mapped/`
- Sample tables: `data/imdg_dgl_sample.json`, `data/psa_dg_groups.json`, `data/segregation_pairs.json`
- Case 1–5 covered by `tests/test_case*.py` (no LLM)

| Case | Expectation |
|------|-------------|
| 1 UN1170 | Forms generated, PSA Group 3 |
| 2 UN1203+UN1830 | `SEGREGATION_CONFLICT`, export blocked |
| 3 UN3105 | Forms generated, PSA Group 1 warning |
| 4 UN3480 | Section IB, Hazcheck + Loss Prevention tags, PSA Group 2 |
| 5 Non-DG | Forms skipped |
