"""Offering "hello" to somebody whose question could not be answered
reads as not having understood that they asked a question."""

from __future__ import annotations

import pytest

from lexmatch import Index, SmallTalk
from tests.chat.small_talk import CONTENT, REPLIES


@pytest.fixture
def index() -> Index:
    return Index([*SmallTalk.entries(REPLIES), *CONTENT])


class TestItStaysOutOfTheSuggestions:
    """Offering "hello" to somebody whose question could not be answered
    reads as not having understood that they asked a question."""

    def test_suggestions_are_content_only(self, index):
        assert index.suggestions(limit=5) == [
            "Are you open to remote work?",
            "What are your rates?",
        ]

    def test_an_index_of_small_talk_alone_still_suggests(self):
        index = Index(SmallTalk.entries({"greeting": "Hello."}))
        assert index.suggestions(limit=2) == ["hello"]

    def test_the_tag_is_what_marks_them(self):
        entry = SmallTalk.entries({"greeting": "Hello."})[0]
        assert "smalltalk" in entry.tags
        assert "greeting" in entry.tags
