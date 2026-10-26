"""A question set as CSV, which is what a spreadsheet exports."""

from __future__ import annotations

import pytest

from lexmatch import CsvParser, Index, ParseError

# Written as lines so the quoted cell does not push a source line over the
# width limit. The quoted answer is the point of the fixture: a comma inside
# a cell is what a hand-rolled splitter gets wrong.
SHEET = "\n".join(
    [
        "Question,Answer,Aliases,Category,Owner",
        'How do I cancel my subscription?,"Settings, then Billing, then Cancel'
        ' plan.",cancel;unsubscribe,billing,ops',
        "Where are my invoices?,Settings then Billing then Invoices."
        ",invoice;receipt,billing,ops",
        "",
    ]
)


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
