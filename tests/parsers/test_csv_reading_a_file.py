"""CSV: reading a file."""

from __future__ import annotations

import pytest

from lexmatch import CsvParser, ParseError
from tests.parsers.csv_is_read import SHEET


class TestReadingAFile:
    def test_a_file_is_read(self, tmp_path):
        path = tmp_path / "faq.csv"
        path.write_text(SHEET, encoding="utf-8")
        assert len(CsvParser.read(path)) == 2

    def test_a_byte_order_mark_is_tolerated(self, tmp_path):
        """Which is what Excel writes."""
        path = tmp_path / "excel.csv"
        path.write_text(SHEET, encoding="utf-8-sig")
        assert len(CsvParser.read(path)) == 2

    def test_a_missing_file_names_the_path(self, tmp_path):
        with pytest.raises(ParseError, match="cannot read"):
            CsvParser.read(tmp_path / "absent.csv")
