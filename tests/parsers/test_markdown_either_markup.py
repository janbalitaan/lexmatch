"""Markdown: the aliases and tags lines, however they are marked up.

Both the italic and the blockquote conventions are how people write a note
to the reader, and a parser that accepts only one makes the other a
configuration format.
"""

from __future__ import annotations

import pytest

from lexmatch import MarkdownParser

BLOCKQUOTE = """\
## What are you working on right now?

> also: current role, what do you do
> tags: work, current

Whatever the owner wants said, in their voice.
"""

ITALIC = """\
## What are you working on right now?

*Also asked: current role, what do you do*

#work #current

Whatever the owner wants said, in their voice.
"""

BARE = """\
## What are you working on right now?

Also asked: current role, what do you do
Tags: work, current

Whatever the owner wants said, in their voice.
"""


class TestEitherMarkupReadsTheSame:
    @pytest.mark.parametrize("page", [BLOCKQUOTE, ITALIC, BARE])
    def test_the_aliases_arrive(self, page):
        assert MarkdownParser.parse(page)[0].aliases == [
            "current role",
            "what do you do",
        ]

    @pytest.mark.parametrize("page", [BLOCKQUOTE, ITALIC, BARE])
    def test_the_tags_arrive(self, page):
        assert MarkdownParser.parse(page)[0].tags == ["work", "current"]

    @pytest.mark.parametrize("page", [BLOCKQUOTE, ITALIC, BARE])
    def test_the_answer_is_only_the_prose(self, page):
        assert MarkdownParser.parse(page)[0].answer == (
            "Whatever the owner wants said, in their voice."
        )

    def test_a_blockquote_hashtag_line_is_read(self):
        page = "## A question?\n\n> #work #current\n\nAn answer.\n"
        assert MarkdownParser.parse(page)[0].tags == ["work", "current"]

    def test_the_tag_openings_are_replaceable(self):
        original = MarkdownParser.TAGGED
        try:
            MarkdownParser.TAGGED = ("labels",)
            page = "## A question?\n\n> labels: one, two\n\nAn answer.\n"
            assert MarkdownParser.parse(page)[0].tags == ["one", "two"]
        finally:
            MarkdownParser.TAGGED = original

    def test_the_default_openings(self):
        assert "tags" in MarkdownParser.TAGGED
        assert "also" in MarkdownParser.ALSO_ASKED
