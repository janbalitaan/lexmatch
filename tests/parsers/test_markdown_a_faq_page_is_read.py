"""Markdown: a faq page is read."""

from __future__ import annotations

from lexmatch import Index, MarkdownParser
from tests.parsers.markdown_is_read import PAGE


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
