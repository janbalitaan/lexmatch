"""CSV: the separator is replaceable."""

from __future__ import annotations

from lexmatch import CsvParser


class TestTheSeparatorIsReplaceable:
    def test_a_different_separator_is_used(self):
        original = CsvParser.SEPARATOR
        try:
            CsvParser.SEPARATOR = "|"
            parsed = CsvParser.parse("question,answer,aliases\nWhat?,A.,one|two\n")
            assert parsed[0].aliases == ["one", "two"]
        finally:
            CsvParser.SEPARATOR = original

    def test_the_default_is_a_semicolon(self):
        assert CsvParser.SEPARATOR == ";"
