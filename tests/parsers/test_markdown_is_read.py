"""A question set as Markdown, which is what a FAQ page already is."""

from __future__ import annotations

import pytest

from lexmatch import Index, MarkdownParser, ParseError

PAGE = """\
# Support

## Are you open to remote work?

Yes, and I have done it for six years.

*Also asked: remote, work from home, wfh*

#hiring #logistics

## What is your notice period?

One month.

*Aliases: notice, when can you start*
"""


class TestAFaqPageIsRead:
    def test_each_heading_becomes_an_entry(self):
        assert len(MarkdownParser.parse(PAGE)) == 2

    def test_the_title_is_not_an_entry(self):
        """A single `#` is the page title, not a question."""
        assert [e.question for e in MarkdownParser.parse(PAGE)] == [
            "Are you open to remote work?",
            "What is your notice period?",
        ]

    def test_the_prose_becomes_the_answer(self):
        assert MarkdownParser.parse(PAGE)[0].answer == (
            "Yes, and I have done it for six years."
        )

    def test_an_also_asked_line_becomes_aliases(self):
        assert MarkdownParser.parse(PAGE)[0].aliases == [
            "remote",
            "work from home",
            "wfh",
        ]

    def test_an_aliases_line_works_too(self):
        assert MarkdownParser.parse(PAGE)[1].aliases == [
            "notice",
            "when can you start",
        ]

    def test_a_hashtag_line_becomes_tags(self):
        assert MarkdownParser.parse(PAGE)[0].tags == ["hiring", "logistics"]

    def test_the_result_is_an_index(self):
        index = Index(MarkdownParser.parse(PAGE))
        assert index.reply("wfh").entry.answer.startswith("Yes")


class TestMultipleParagraphs:
    def test_they_are_joined(self):
        page = "## What do you do?\n\nFirst line.\n\nSecond line.\n"
        assert MarkdownParser.parse(page)[0].answer == "First line. Second line."


class TestWhatIsRefused:
    def test_a_page_with_no_headings_says_what_is_needed(self):
        with pytest.raises(ParseError, match="no level-2 headings"):
            MarkdownParser.parse("Just some prose with no questions in it.\n")

    def test_a_heading_with_no_answer_names_its_line(self):
        page = "# Title\n\n## A question with nothing under it?\n"
        with pytest.raises(ParseError, match="line 3"):
            MarkdownParser.parse(page)


class TestReadingAFile:
    def test_a_file_is_read(self, tmp_path):
        path = tmp_path / "faq.md"
        path.write_text(PAGE, encoding="utf-8")
        assert len(MarkdownParser.read(path)) == 2

    def test_a_missing_file_names_the_path(self, tmp_path):
        with pytest.raises(ParseError, match="cannot read"):
            MarkdownParser.read(tmp_path / "absent.md")


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
