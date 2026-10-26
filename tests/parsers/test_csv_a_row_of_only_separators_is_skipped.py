"""A spreadsheet writes a line of empty cells for a spacer row, and
`csv` reads it as a dict of empty strings rather than nothing at all."""

from __future__ import annotations

from lexmatch import CsvParser


class TestARowOfOnlySeparatorsIsSkipped:
    """A spreadsheet writes a line of empty cells for a spacer row, and
    `csv` reads it as a dict of empty strings rather than nothing at all."""

    def test_it_does_not_become_an_entry(self):
        sheet = "question,answer,aliases\nWhat is this?,A bot.,bot\n,,\n"
        assert len(CsvParser.parse(sheet)) == 1

    def test_several_spacer_rows_are_all_skipped(self):
        sheet = "question,answer\n,\nWhat is this?,A bot.\n,\n,\n"
        parsed = CsvParser.parse(sheet)
        assert len(parsed) == 1
        assert parsed[0].question == "What is this?"
