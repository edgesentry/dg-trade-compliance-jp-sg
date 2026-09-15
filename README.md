# dg-trade-compliance-jp-sg

Dangerous-goods (DG) trade compliance prototype for **Japan → Singapore** export workflows.

Strategy source (commercial docs):  
`edgesentry-commercial/docs/strategy/dg-trade-compliance-jp-sg/`  
(`mvp.md` · `prototype-plan.md`)

This repo implements the runnable Neuro-Symbolic stack. **Currently shipped: Multimodal Extract (LiteLLM).**

---

## Status

| Module | Status |
|--------|--------|
| **Multimodal Extract** (Vision/text → UN / PSN / Class / PG / FP + evidence) | **Implemented** (LiteLLM) |
| Ontology Map (IMDG canonical → 白紙/赤紙/CyberPort/PSA) | Planned |
| Responsible HITL | Planned |
| Audit WORM (SHA-256 envelope interface) | Planned |

---

## Multimodal Extract (LiteLLM)

Probabilistic slot fill + evidence citations.  
Providers via LiteLLM: **Gemini · OpenAI · Anthropic** (model id only — no provider-specific clients).

**Default model:** `gemini/gemini-3.8-flash`

### Setup

Requires **Python ≥ 3.13**.

```bash
cd dg-trade-compliance-jp-sg
uv sync --python 3.13
cp .env.example .env
# edit .env: GEMINI_API_KEY (or OPENAI_API_KEY / ANTHROPIC_API_KEY)
```

### LiteLLM proxy

```bash
./scripts/start_litellm.sh
# → http://127.0.0.1:4000/v1  (Bearer sk-dg-local)
# config: litellm_config.yaml
```

Point extract at the proxy (optional):

```bash
export LITELLM_API_BASE=http://127.0.0.1:4000
export LITELLM_MASTER_KEY=sk-dg-local
uv run dg-compliance extract data/samples/sds_un1170_ethanol.txt
```

### Run

```bash
# Text SDS fixture (Case 1) — uses Gemini 3.8 Flash by default
uv run dg-compliance extract data/samples/sds_un1170_ethanol.txt -o dist/extract_un1170.json

# OpenAI / Anthropic
uv run dg-compliance extract data/samples/sds_un1170_ethanol.txt -m openai/gpt-4o
uv run dg-compliance extract data/samples/sds_un1170_ethanol.txt \
  -m anthropic/claude-sonnet-4-20250514

# PDF / scanned image (vision)
uv run dg-compliance extract path/to/sds.pdf

# Optional shipping chat/email context
uv run dg-compliance extract data/samples/sds_un1170_ethanol.txt \
  --instruction-text "門司出港 ONE便、ドラム20本、シンガポール向け"
```

```bash
uv run dg-compliance models   # provider / model help
uv run pytest -v              # offline schema tests (no API key)
```

### Env

| Variable | Purpose |
|----------|---------|
| `DG_EXTRACT_MODEL` | LiteLLM model id (default `gemini/gemini-3.8-flash`) |
| `GEMINI_API_KEY` | Google AI Studio (Gemini) |
| `OPENAI_API_KEY` | OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic |

### Output shape

`ExtractionResult` JSON: `fields` (UN, PSN, class, PG, flash point, marine pollutant, packaging, is_dg) + `evidence[]` (`field`, `page_no`, `snippet`) for HITL highlight later.

---

## Layout

```text
scripts/start_litellm.sh   # LiteLLM proxy launcher
litellm_config.yaml        # Gemini / OpenAI / Anthropic model list
src/dg_compliance/
  cli.py
  models/extraction.py
  extract/
    litellm_extractor.py   # LiteLLM completion (direct or via proxy)
    pdf_pages.py           # PDF/image → data-URL pages
    prompts.py
data/samples/              # synthetic SDS text fixtures
tests/                     # offline unit tests
```

See [MVP_IMPLEMENTATION_PLAN.md](MVP_IMPLEMENTATION_PLAN.md) for the full roadmap.
