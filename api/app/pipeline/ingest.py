"""Local OCR intake for the private reference set.

Runs entirely on-machine (Tesseract) — the scan text is never sent to a model,
committed, or shown to a user. It OCRs each page to a local .txt and proposes a
draft list of candidate topic headings the human tidies into concepts. Only the
concept names the human keeps (facts/topic labels) ever go on to generation; the
book's wording stays here, local and gitignored.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_IMG_EXT = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".bmp"}
_PAGE_NOISE = re.compile(r"^\s*(page\s*\d+|\d+|[ivxlcdm]+)\s*$", re.I)
_LEAD = re.compile(r"^(chapter|lesson|unit|topic)\b", re.I)


@dataclass(frozen=True)
class OcrPage:
    image: Path
    text: str


def heading_candidates(text: str) -> list[str]:
    """Heuristic, model-free guess at headings/topics in a page of OCR text:
    short lines, mostly letters, Title Case / ALL CAPS / a 'Chapter|Lesson|…'
    lead, and no sentence-ending punctuation. Rough on purpose — a starting
    point for the human, not an answer."""
    out: list[str] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip().strip("•*-—–·").strip()
        if not line or _PAGE_NOISE.match(line):
            continue
        words = line.split()
        if not (1 < len(words) <= 7):
            continue
        letters = sum(c.isalpha() for c in line)
        if letters < max(3, 0.6 * len(line.replace(" ", ""))):
            continue
        if line[-1] in ".,;:?!":
            continue
        looks_heading = line == line.title() or line.isupper() or bool(_LEAD.match(line))
        if not looks_heading:
            continue
        key = line.lower()
        if key not in seen:
            seen.add(key)
            out.append(line)
    return out


def ocr_pages(root: Path) -> list[OcrPage]:
    import pytesseract
    from PIL import Image

    pages: list[OcrPage] = []
    for img in sorted(p for p in root.rglob("*") if p.suffix.lower() in _IMG_EXT):
        pages.append(OcrPage(image=img, text=pytesseract.image_to_string(Image.open(img))))
    return pages


def build_outline(pages: list[OcrPage]) -> str:
    """A draft, editable outline of candidate topics across the pages."""
    lines = [
        "# Proposed concept outline (DRAFT — edit me)",
        f"# Local OCR of {len(pages)} page(s). Nothing here was sent to a model.",
        "# Keep the topic names you want as concepts, delete the rest, fix wording.",
        "# Only the names you keep go on to generation.",
        "",
        "## Candidate topics",
    ]
    all_headings: list[str] = []
    seen: set[str] = set()
    for page in pages:
        for h in heading_candidates(page.text):
            if h.lower() not in seen:
                seen.add(h.lower())
                all_headings.append(h)
    if all_headings:
        lines += [f"- {h}" for h in all_headings]
    else:
        lines.append("- (none detected — add topic names from the .txt files by hand)")
    return "\n".join(lines) + "\n"


def run_ingest(root: Path, *, log=print) -> dict:
    """OCR every image under `root`, write a local .txt beside each, and write a
    draft `_outline.md`. All outputs stay under `root` (gitignored)."""
    if not root.exists():
        raise FileNotFoundError(f"{root} does not exist — create it and add scans locally (it is gitignored).")

    pages = ocr_pages(root)
    if not pages:
        log(f"No images found under {root}.")
        return {"pages": 0, "topics": 0}

    for page in pages:
        page.image.with_suffix(".txt").write_text(page.text, encoding="utf-8")

    outline = build_outline(pages)
    outline_path = root / "_outline.md"
    outline_path.write_text(outline, encoding="utf-8")

    topics = outline.count("\n- ")
    log(f"OCR'd {len(pages)} page(s) locally → .txt beside each (never committed or prompted).")
    log(f"Draft outline with ~{topics} candidate topic(s): {outline_path}")
    log("Edit it down to the concepts you want, then we generate original content from those names.")
    return {"pages": len(pages), "topics": topics}
