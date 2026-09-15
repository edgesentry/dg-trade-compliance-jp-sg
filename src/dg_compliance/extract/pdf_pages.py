"""Render PDF / image sources into LiteLLM vision content parts."""

from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}
TEXT_SUFFIXES = {".txt", ".md", ".csv", ".json"}
PDF_SUFFIXES = {".pdf"}


def _png_data_url(image: Image.Image, *, max_edge: int = 2048) -> str:
    img = image.convert("RGB")
    w, h = img.size
    scale = min(1.0, max_edge / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def pdf_to_data_urls(path: Path, *, max_pages: int = 8, scale: float = 2.0) -> list[str]:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(path))
    urls: list[str] = []
    n = min(len(pdf), max_pages)
    for i in range(n):
        page = pdf[i]
        bitmap = page.render(scale=scale)
        pil = bitmap.to_pil()
        urls.append(_png_data_url(pil))
    return urls


def image_to_data_url(path: Path) -> str:
    with Image.open(path) as im:
        return _png_data_url(im)


def build_user_content(
    path: Path,
    *,
    instruction_text: str | None,
    user_prompt: str,
    max_pages: int = 8,
) -> list[dict]:
    """Build OpenAI-style multimodal content list for litellm.completion."""
    suffix = path.suffix.lower()
    parts: list[dict] = [{"type": "text", "text": user_prompt}]

    if suffix in PDF_SUFFIXES:
        for i, url in enumerate(pdf_to_data_urls(path, max_pages=max_pages), start=1):
            parts.append({"type": "text", "text": f"[Source page {i}]"})
            parts.append({"type": "image_url", "image_url": {"url": url}})
    elif suffix in IMAGE_SUFFIXES:
        parts.append({"type": "text", "text": "[Source page 1]"})
        parts.append(
            {"type": "image_url", "image_url": {"url": image_to_data_url(path)}}
        )
    elif suffix in TEXT_SUFFIXES or suffix == "":
        text = path.read_text(encoding="utf-8", errors="replace")
        parts.append(
            {
                "type": "text",
                "text": f"[Source document text]\n{text}",
            }
        )
    else:
        # Try as text fallback
        text = path.read_text(encoding="utf-8", errors="replace")
        parts.append({"type": "text", "text": f"[Source document text]\n{text}"})

    if instruction_text and instruction_text.strip():
        # already embedded in user_prompt template; keep a reminder
        pass

    return parts
