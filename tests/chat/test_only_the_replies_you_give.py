"""Only the replies you give."""

from __future__ import annotations

import pytest

from lexmatch import Index, SmallTalk
from lexmatch.exceptions import SmallTalkError
from tests.chat.small_talk import CONTENT, REPLIES


@pytest.fixture
def index() -> Index:
    return Index([*SmallTalk.entries(REPLIES), *CONTENT])


class TestOnlyTheRepliesYouGive:
    def test_an_intent_without_a_reply_is_not_added(self):
        entries = SmallTalk.entries({"greeting": "Hello."})
        assert len(entries) == 1
        assert Index(entries).answer("thanks")[0] is None

    def test_an_empty_reply_is_skipped(self):
        assert SmallTalk.entries({"greeting": "Hello.", "thanks": "   "}) == [
            *SmallTalk.entries({"greeting": "Hello."})
        ]

    def test_nothing_given_builds_nothing(self):
        assert SmallTalk.entries({}) == []

    def test_an_unknown_intent_raises(self):
        """A typo leaves the handler silently absent, which looks exactly
        like one that works until somebody says hello."""
        with pytest.raises(SmallTalkError, match="no such small-talk intent"):
            SmallTalk.entries({"greetings": "Hello."})

    def test_the_message_lists_what_is_available(self):
        with pytest.raises(SmallTalkError, match="greeting"):
            SmallTalk.entries({"nope": "Hello."})
