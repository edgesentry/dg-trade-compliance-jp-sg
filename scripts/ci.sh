#!/usr/bin/env bash
# Local CI parity with .github/workflows/ci.yml
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> uv sync"
uv sync --python 3.13 --extra dev

echo "==> ruff check"
uv run ruff check src tests

echo "==> ruff format --check"
uv run ruff format --check src tests

echo "==> mypy"
uv run mypy src

echo "==> bandit"
uv run bandit -r src -c pyproject.toml -q

echo "==> pip-audit"
export PIP_AUDIT_CACHE_DIR="${PIP_AUDIT_CACHE_DIR:-$ROOT/.cache/pip-audit}"
mkdir -p "$PIP_AUDIT_CACHE_DIR"
uv run pip-audit --progress-spinner off --cache-dir "$PIP_AUDIT_CACHE_DIR"

echo "==> pytest"
uv run pytest -v --tb=short

echo "CI checks passed."
