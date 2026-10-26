"""A question set that is being edited while it is served.

The strict default is right for a file loaded once at startup: it should say
what is wrong rather than quietly hold fewer answers than it appears to.

It is wrong for a file somebody is editing *now*. A question set reloaded on
change should keep answering while the owner is halfway through adding the
next question — and a heading with nothing under it yet is what halfway looks
like. Raising there takes the whole bot down over an unfinished sentence.
"""

from __future__ import annotations

import json

import pytest

from lexmatch import CsvParser, Index, JsonParser, MarkdownParser, ParseError

HALF_WRITTEN_MARKDOWN = """\
## Are you open to remote work?

Yes, and I have done it for six years.

## What is your notice period?
"""

HALF_WRITTEN_JSON = json.dumps(
    [
        {"question": "Are you open to remote work?", "answer": "Yes."},
        {"question": "What is your notice period?"},
        {"question": "What are your rates?", "answer": "It depends."},
    ]
)

HALF_WRITTEN_CSV = "question,answer\nAre you open to remote work?,Yes.\nWhat next?,\n"


class TestStrictIsTheDefault:
    def test_markdown_raises(self):
        with pytest.raises(ParseError):
            MarkdownParser.parse(HALF_WRITTEN_MARKDOWN)

    def test_json_raises(self):
        with pytest.raises(ParseError):
            JsonParser.parse(HALF_WRITTEN_JSON)

    def test_csv_raises(self):
        with pytest.raises(ParseError):
            CsvParser.parse(HALF_WRITTEN_CSV)


class TestLenientKeepsWhatIsFinished:
    def test_markdown_keeps_the_finished_entry(self):
        kept = MarkdownParser.parse(HALF_WRITTEN_MARKDOWN, strict=False)
        assert [entry.question for entry in kept] == ["Are you open to remote work?"]

    def test_json_keeps_both_finished_entries(self):
        kept = JsonParser.parse(HALF_WRITTEN_JSON, strict=False)
        assert [entry.question for entry in kept] == [
            "Are you open to remote work?",
            "What are your rates?",
        ]

    def test_csv_keeps_the_finished_row(self):
        kept = CsvParser.parse(HALF_WRITTEN_CSV, strict=False)
        assert [entry.question for entry in kept] == ["Are you open to remote work?"]

    def test_the_bot_still_answers(self):
        """Which is the whole point of the option."""
        index = Index(MarkdownParser.parse(HALF_WRITTEN_MARKDOWN, strict=False))
        assert index.reply("remote work").answered


class TestWhatIsAlwaysAnError:
    """Something there is no way to skip past."""

    def test_json_that_is_not_json(self):
        with pytest.raises(ParseError):
            JsonParser.parse("{not json", strict=False)

    def test_a_csv_with_no_usable_header(self):
        with pytest.raises(ParseError, match="header"):
            CsvParser.parse("title,body\nsomething,else\n", strict=False)

    def test_markdown_with_no_headings(self):
        with pytest.raises(ParseError, match="no level-2 headings"):
            MarkdownParser.parse("Just prose.\n", strict=False)


class TestReadPassesItThrough:
    def test_markdown(self, tmp_path):
        path = tmp_path / "faq.md"
        path.write_text(HALF_WRITTEN_MARKDOWN, encoding="utf-8")
        assert len(MarkdownParser.read(path, strict=False)) == 1
        with pytest.raises(ParseError):
            MarkdownParser.read(path)

    def test_json(self, tmp_path):
        path = tmp_path / "faq.json"
        path.write_text(HALF_WRITTEN_JSON, encoding="utf-8")
        assert len(JsonParser.read(path, strict=False)) == 2

    def test_csv(self, tmp_path):
        path = tmp_path / "faq.csv"
        path.write_text(HALF_WRITTEN_CSV, encoding="utf-8")
        assert len(CsvParser.read(path, strict=False)) == 1
