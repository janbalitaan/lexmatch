"""CSV: what is forgiven."""

from __future__ import annotations

import pytest

from lexmatch import CsvParser
from tests.parsers.csv_is_read import SHEET


class TestWhatIsForgiven:
    def test_a_blank_row_is_skipped(self):
        """Which is what a trailing newline or a spacer row looks like."""
        with_gap = SHEET.replace("Where are", "\nWhere are")
        assert len(CsvParser.parse(with_gap)) == 2

    def test_extra_columns_are_ignored(self):
        assert CsvParser.parse(SHEET)[0].question.startswith("How do I cancel")

    def test_the_header_is_matched_case_insensitively(self):
        lowered = SHEET.replace("Question,Answer,Aliases", "question,answer,aliases")
        assert len(CsvParser.parse(lowered)) == 2

    @pytest.mark.parametrize(
        ("header", "expected"),
        [("q,a", "Short"), ("prompt,response", "Short"), ("Question,Answer", "Short")],
    )
    def test_short_column_names_are_accepted(self, header, expected):
        parsed = CsvParser.parse(f"{header}\nWhat is this?,{expected}\n")
        assert parsed[0].answer == expected

    def test_whitespace_around_cells_is_trimmed(self):
        parsed = CsvParser.parse("question,answer\n  What is this?  ,  A bot.  \n")
        assert parsed[0].question == "What is this?"
        assert parsed[0].answer == "A bot."
