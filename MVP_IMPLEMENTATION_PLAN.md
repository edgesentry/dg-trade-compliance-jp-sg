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
| **Theme ①** | Multimodal Extract via **LiteLLM** (Gemini / OpenAI / Anthropic), evidence page+snippet | **Done** |
| Theme ② | Ontology Map + projections | Next |
| Theme ③ | HITL preview + export-only | Later |
| Demo suite | Case 1–5 | After Ontology Map |

**Default extract model:** `gemini/gemini-3.8-flash`

---

## Theme ① — current design

- Entry: `uv run dg-compliance extract <sds.pdf|txt|image>`
- Transport: `litellm.completion` with `DG_EXTRACT_MODEL` / `--model`
- Providers: `gemini/*` · `openai/*` · `anthropic/*`
- PDF pages rendered with `pypdfium2` → PNG data-URLs for vision models
- Schema: `ExtractionResult` / `ExtractedDgFields` / `EvidenceCitation` in `models/extraction.py`
- Package path: `src/dg_compliance/extract/`

Extract **must not** emit PSA Group or segregation verdicts.

---

## Next (Theme ② sketch)

```text
ExtractionResult
    → CanonicalImdgItem
    → hakushi / akagami / cyberport JSON / psa_group + PAN
    → segregation check on co-load
```

Benchmark cases remain those in `prototype-plan.md` §3 (UN1170, segregation, PSA G1, LiB, non-DG).
