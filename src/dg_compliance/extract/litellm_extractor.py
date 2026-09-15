"""Multimodal Extract via LiteLLM (Anthropic / OpenAI / Gemini)."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from litellm import completion
from pydantic import ValidationError

from dg_compliance.extract.base import BaseExtractor
from dg_compliance.extract.pdf_pages import build_user_content
from dg_compliance.extract.prompts import (
    SYSTEM_PROMPT,
    USER_INSTRUCTION_TEMPLATE,
)
from dg_compliance.models.extraction import (
    EvidenceCitation,
    ExtractedDgFields,
    ExtractionResult,
)

# Default: Gemini 3.8 Flash via Google AI Studio (GEMINI_API_KEY)
DEFAULT_MODEL = "gemini/gemini-3.8-flash"

# Documented / supported provider prefixes (LiteLLM routes)
SUPPORTED_PROVIDERS = (
    "gemini",  # Google AI Studio — GEMINI_API_KEY
    "openai",  # OpenAI — OPENAI_API_KEY
    "anthropic",  # Anthropic — ANTHROPIC_API_KEY
)

EXAMPLE_MODELS = (
    "gemini/gemini-3.8-flash",
    "openai/gpt-4o",
    "anthropic/claude-sonnet-4-20250514",
)


def resolve_model(explicit: str | None = None) -> str:
    return (
        explicit
        or os.getenv("DG_EXTRACT_MODEL")
        or os.getenv("LITELLM_MODEL")
        or DEFAULT_MODEL
    )


def provider_of(model: str) -> str | None:
    """Return LiteLLM provider prefix if present (gemini / openai / anthropic)."""
    if "/" not in model:
        return None
    prefix = model.split("/", 1)[0].lower()
    return prefix if prefix in SUPPORTED_PROVIDERS else prefix


def _is_gemini3_plus(model: str) -> bool:
    """Gemini 3+ rejects/deprecates temperature, top_p, top_k sampling params."""
    slug = model.rsplit("/", 1)[-1].lower()
    return slug.startswith("gemini-3")


def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()


def _parse_payload(raw: str) -> dict[str, Any]:
    cleaned = _strip_fences(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # best-effort: find outermost object
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start >= 0 and end > start:
            data = json.loads(cleaned[start : end + 1])
        else:
            raise
    if not isinstance(data, dict):
        raise ValueError("Model response JSON root must be an object")
    return data


class LiteLLMExtractor(BaseExtractor):
    """
    Vision/text extract through LiteLLM.

    Supported providers (swap via model id only):
      - gemini/gemini-3.8-flash          (default; GEMINI_API_KEY)
      - openai/gpt-4o                    (OPENAI_API_KEY)
      - anthropic/claude-sonnet-4-...    (ANTHROPIC_API_KEY)
    """

    def __init__(
        self,
        model: str | None = None,
        *,
        temperature: float = 0.0,
        max_pages: int = 8,
        max_tokens: int = 4096,
        load_env: bool = True,
    ) -> None:
        if load_env:
            load_dotenv()
        self.model = resolve_model(model)
        self.temperature = temperature
        self.max_pages = max_pages
        self.max_tokens = max_tokens

    def extract(
        self, source: Path, *, instruction_text: str | None = None
    ) -> ExtractionResult:
        source = source.resolve()
        if not source.is_file():
            raise FileNotFoundError(source)

        user_text = USER_INSTRUCTION_TEMPLATE.format(
            instruction_text=(instruction_text or "(none)").strip()
        )
        content = build_user_content(
            source,
            instruction_text=instruction_text,
            user_prompt=user_text,
            max_pages=self.max_pages,
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
        }
        # Gemini 3+: temperature/top_p/top_k are deprecated — keep determinism in system prompt
        if not _is_gemini3_plus(self.model):
            kwargs["temperature"] = self.temperature
        # Optional: route through local LiteLLM proxy (./scripts/start_litellm.sh)
        api_base = os.getenv("LITELLM_API_BASE") or os.getenv("OPENAI_BASE_URL")
        if api_base:
            kwargs["api_base"] = api_base.rstrip("/")
            kwargs["api_key"] = (
                os.getenv("LITELLM_MASTER_KEY")
                or os.getenv("LITELLM_API_KEY")
                or "sk-dg-local"
            )
        try:
            response = completion(**kwargs)
        except Exception:
            # Some providers reject response_format; retry without it.
            kwargs.pop("response_format", None)
            response = completion(**kwargs)

        raw = response.choices[0].message.content or ""
        warnings: list[str] = []
        try:
            payload = _parse_payload(raw)
        except (json.JSONDecodeError, ValueError) as e:
            return ExtractionResult(
                source_path=str(source),
                model=self.model,
                fields=ExtractedDgFields(),
                evidence=[],
                raw_model_text=raw,
                warnings=[f"Failed to parse model JSON: {e}"],
            )

        fields_raw = payload.get("fields") or {}
        evidence_raw = payload.get("evidence") or []
        warnings.extend(str(w) for w in (payload.get("warnings") or []))

        try:
            fields = ExtractedDgFields.model_validate(fields_raw)
        except ValidationError as e:
            warnings.append(f"Field validation issues (partial apply): {e}")
            # coerce what we can
            fields = ExtractedDgFields.model_validate(
                {k: fields_raw.get(k) for k in ExtractedDgFields.model_fields}
            )

        evidence: list[EvidenceCitation] = []
        for item in evidence_raw:
            try:
                evidence.append(EvidenceCitation.model_validate(item))
            except ValidationError as e:
                warnings.append(f"Skipped invalid evidence item: {e}")

        return ExtractionResult(
            source_path=str(source),
            model=self.model,
            fields=fields,
            evidence=evidence,
            raw_model_text=raw,
            warnings=warnings,
        )
