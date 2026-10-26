"""Markdown: multiple paragraphs."""

from __future__ import annotations

from lexmatch import MarkdownParser


class TestMultipleParagraphs:
    def test_they_are_joined(self):
        page = "## What do you do?\n\nFirst line.\n\nSecond line.\n"
        assert MarkdownParser.parse(page)[0].answer == "First line. Second line."
