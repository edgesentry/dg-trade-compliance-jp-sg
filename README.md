# dg-trade-compliance-jp-sg

Dangerous-goods (DG) trade compliance prototype for **Japan → Singapore** export workflows.

Strategy source (commercial docs):  
`edgesentry-commercial/docs/strategy/dg-trade-compliance-jp-sg/`  
(`mvp.md` · `prototype-plan.md`)

This repo implements the runnable Neuro-Symbolic stack: **Multimodal Extract (LiteLLM)** + **Ontology Map**.

---

## Status

| Module | Status |
|--------|--------|
| **Multimodal Extract** (Vision/text → UN / PSN / Class / PG / FP + evidence) | **Implemented** (LiteLLM) |
| **Ontology Map** (IMDG canonical → 白紙/赤紙/CyberPort/PSA/PAN + segregation) | **Implemented** |
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

### Extract

```bash
uv run dg-compliance extract data/samples/sds_un1170_ethanol.txt -o dist/extract_un1170.json
uv run dg-compliance extract data/samples/sds_un1170_ethanol.txt -m openai/gpt-4o
```

---

## Ontology Map (deterministic)

Maps `ExtractionResult` JSON → canonical IMDG → 白紙 / 赤紙 / CyberPort JSON / PSA Group / PAN.  
Segregation conflicts set `export_blocked` and skip form files (exit code 2).

```bash
# After extract
uv run dg-compliance map dist/extract_un1170.json -o dist/mapped/

# Co-load (Case 2 segregation)
uv run dg-compliance map dist/gas.json --co-load dist/acid.json -o dist/mapped/

# Lithium Wh override (Case 4)
uv run dg-compliance map dist/battery.json --watt-hour 120 -o dist/mapped/
```

Offline Case 1–5 suite (no API key):

```bash
uv run pytest -v
```

---

## Env

| Variable | Purpose |
|----------|---------|
| `DG_EXTRACT_MODEL` | LiteLLM model id (default `gemini/gemini-3.8-flash`) |
| `GEMINI_API_KEY` | Google AI Studio (Gemini) |
| `OPENAI_API_KEY` | OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic |
| `LITELLM_API_BASE` | Optional local proxy base |

---

## Layout

```text
scripts/start_litellm.sh
litellm_config.yaml
src/dg_compliance/
  cli.py
  models/extraction.py
  models/canonical.py
  extract/                 # Multimodal Extract
  ontology/                # map + pipeline
  validate/                # IMDG / segregation / PSA / lithium
  projections/             # hakushi / akagami / cyberport / pan
data/
  imdg_dgl_sample.json
  psa_dg_groups.json
  segregation_pairs.json
  samples/
tests/                     # schema + Case 1–5
```

See [MVP_IMPLEMENTATION_PLAN.md](MVP_IMPLEMENTATION_PLAN.md) for the full roadmap.
