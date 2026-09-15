#!/usr/bin/env bash
# Start LiteLLM proxy (Gemini / OpenAI / Anthropic) for DG Multimodal Extract.
#
# Usage:
#   ./scripts/start_litellm.sh
#   ./scripts/start_litellm.sh --detailed_debug
#   LITELLM_PORT=4001 ./scripts/start_litellm.sh
#
# Endpoint: http://localhost:4000/v1
# Auth:     Authorization: Bearer sk-dg-local  (see litellm_config.yaml)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

HOST="${LITELLM_HOST:-0.0.0.0}"
PORT="${LITELLM_PORT:-4000}"
CONFIG="${LITELLM_CONFIG:-$ROOT/litellm_config.yaml}"

if [[ ! -f "$CONFIG" ]]; then
  echo "error: config not found: $CONFIG" >&2
  exit 1
fi

# Warn if no provider keys are set (proxy will still start)
if [[ -z "${GEMINI_API_KEY:-}" && -z "${OPENAI_API_KEY:-}" && -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "warning: none of GEMINI_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY are set." >&2
  echo "         Put keys in .env (see .env.example) before calling models." >&2
fi

echo "LiteLLM proxy"
echo "  config: $CONFIG"
echo "  listen: http://${HOST}:${PORT}"
echo "  OpenAI-compatible base: http://127.0.0.1:${PORT}/v1"
echo "  master key: ${LITELLM_MASTER_KEY:-sk-dg-local}"
echo "  default model alias: gemini-3.8-flash"
echo ""

# Prefer project venv; fall back to uv run
if [[ -x "$ROOT/.venv/bin/litellm" ]]; then
  exec "$ROOT/.venv/bin/litellm" --config "$CONFIG" --host "$HOST" --port "$PORT" "$@"
fi

exec uv run litellm --config "$CONFIG" --host "$HOST" --port "$PORT" "$@"
