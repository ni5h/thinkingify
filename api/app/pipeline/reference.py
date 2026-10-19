"""Loads the private reference set for local dedupe.

The folder is gitignored and never committed, shown, or put in a prompt. These
texts are only ever embedded locally (see dedupe) — they must not be passed to
any model.
"""
from __future__ import annotations

from pathlib import Path

from app.core.config import settings


def reference_path() -> Path:
    return Path(settings.reference_dir)


def load_reference_texts() -> list[str]:
    root = reference_path()
    if not root.exists():
        return []
    return [f.read_text(encoding="utf-8", errors="ignore") for f in sorted(root.rglob("*.txt"))]
