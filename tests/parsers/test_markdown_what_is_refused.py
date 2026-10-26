"""Markdown: what is refused."""

from __future__ import annotations

import pytest

from lexmatch import MarkdownParser, ParseError


class TestWhatIsRefused:
    def test_a_page_with_no_headings_says_what_is_needed(self):
        with pytest.raises(ParseError, match="no level-2 headings"):
            MarkdownParser.parse("Just some prose with no questions in it.\n")

    def test_a_heading_with_no_answer_names_its_line(self):
        page = "# Title\n\n## A question with nothing under it?\n"
        with pytest.raises(ParseError, match="line 3"):
            MarkdownParser.parse(page)
