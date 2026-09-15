"""Base extractor interface (probabilistic multimodal extract)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from dg_compliance.models.extraction import ExtractionResult


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, source: Path, *, instruction_text: str | None = None) -> ExtractionResult:
        """Extract DG slots + evidence from a SDS PDF/image/text file."""
