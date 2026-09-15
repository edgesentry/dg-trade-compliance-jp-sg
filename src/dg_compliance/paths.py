"""Resolve paths to bundled reference data JSON files."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


def repo_root() -> Path:
    # src/dg_compliance/paths.py → parents[2] = repo root (dev layout)
    here = Path(__file__).resolve()
    candidate = here.parents[2]
    if (candidate / "data" / "imdg_dgl_sample.json").is_file():
        return candidate
    cwd = Path.cwd()
    if (cwd / "data" / "imdg_dgl_sample.json").is_file():
        return cwd
    return candidate


def data_dir() -> Path:
    return repo_root() / "data"


@lru_cache(maxsize=1)
def imdg_dgl_path() -> Path:
    return data_dir() / "imdg_dgl_sample.json"


@lru_cache(maxsize=1)
def psa_groups_path() -> Path:
    return data_dir() / "psa_dg_groups.json"


@lru_cache(maxsize=1)
def segregation_path() -> Path:
    return data_dir() / "segregation_pairs.json"
