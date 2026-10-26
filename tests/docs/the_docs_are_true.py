"""Fixtures the tests split out of the_docs_are_true share.

The data for "the docs are true", kept in one place so that reducing each
test file to a single class did not mean copying it.
"""

from __future__ import annotations

from pathlib import Path

DOCS = Path(__file__).resolve().parents[2] / "docs"

PAGES = sorted(DOCS.glob("*.md"))
