"""CSV: an exported sheet is read."""

from __future__ import annotations

from lexmatch import CsvParser, Index
from tests.parsers.csv_is_read import SHEET


class TestAnExportedSheetIsRead:
    def test_every_row_becomes_an_entry(self):
        assert len(CsvParser.parse(SHEET)) == 2

    def test_a_quoted_cell_containing_commas_survives(self):
        """The reason this uses the csv module rather than splitting."""
        first = CsvParser.parse(SHEET)[0]
        assert first.answer == "Settings, then Billing, then Cancel plan."

    def test_several_aliases_in_one_cell_are_split(self):
        assert CsvParser.parse(SHEET)[0].aliases == ["cancel", "unsubscribe"]

    def test_a_category_column_becomes_tags(self):
        assert CsvParser.parse(SHEET)[0].tags == ["billing"]

    def test_the_result_is_an_index(self):
        index = Index(CsvParser.parse(SHEET))
        assert index.reply("how do i cancel").entry.answer.startswith("Settings")
