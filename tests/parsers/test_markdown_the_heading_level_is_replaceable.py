"""Markdown: the heading level is replaceable."""

from __future__ import annotations

from lexmatch import MarkdownParser


class TestTheHeadingLevelIsReplaceable:
    def test_a_different_level_is_used(self):
        original = MarkdownParser.LEVEL
        try:
            MarkdownParser.LEVEL = 3
            page = "## Section\n\n### A question?\n\nAn answer.\n"
            assert MarkdownParser.parse(page)[0].question == "A question?"
        finally:
            MarkdownParser.LEVEL = original

    def test_the_default_is_two(self):
        assert MarkdownParser.LEVEL == 2
