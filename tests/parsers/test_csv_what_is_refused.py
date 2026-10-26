"""CSV: what is refused."""

from __future__ import annotations

import pytest

from lexmatch import CsvParser, ParseError


class TestWhatIsRefused:
    def test_an_empty_file_says_so(self):
        with pytest.raises(ParseError, match="no header row"):
            CsvParser.parse("")

    def test_a_header_without_a_question_column_lists_what_was_found(self):
        with pytest.raises(ParseError, match="found 'title', 'body'"):
            CsvParser.parse("title,body\nsomething,else\n")

    def test_a_row_with_no_question_names_its_line(self):
        """Counted the way a spreadsheet counts, header included."""
        with pytest.raises(ParseError, match="line 3"):
            CsvParser.parse("question,answer\nWhat is this?,A bot.\n,orphaned\n")
