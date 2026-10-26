"""Markdown: reading a file."""

from __future__ import annotations

import pytest

from lexmatch import MarkdownParser, ParseError
from tests.parsers.markdown_is_read import PAGE


class TestReadingAFile:
    def test_a_file_is_read(self, tmp_path):
        path = tmp_path / "faq.md"
        path.write_text(PAGE, encoding="utf-8")
        assert len(MarkdownParser.read(path)) == 2

    def test_a_missing_file_names_the_path(self, tmp_path):
        with pytest.raises(ParseError, match="cannot read"):
            MarkdownParser.read(tmp_path / "absent.md")
