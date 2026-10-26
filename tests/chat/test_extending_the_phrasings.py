"""Extending the phrasings."""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index, SmallTalk
from lexmatch.exceptions import SmallTalkError
from tests.chat.small_talk import CONTENT, REPLIES


@pytest.fixture
def index() -> Index:
    return Index([*SmallTalk.entries(REPLIES), *CONTENT])


class TestExtendingThePhrasings:
    def test_the_phrasings_are_available(self):
        assert "hiya" in SmallTalk.phrasings_for("greeting")

    def test_an_unknown_intent_raises(self):
        with pytest.raises(SmallTalkError, match="no such small-talk intent"):
            SmallTalk.phrasings_for("nope")

    def test_the_intents_are_listed(self):
        assert "greeting" in SmallTalk.INTENTS
        assert len(SmallTalk.INTENTS) == 6

    def test_a_caller_can_build_on_them(self):
        phrasings = SmallTalk.phrasings_for("greeting")
        entry = Entry(
            question=phrasings[0],
            answer="Aloha!",
            aliases=[*phrasings[1:], "aloha", "salut"],
        )
        assert Index([entry]).answer("salut")[0] is not None
        assert Index([entry]).answer("hiya")[0] is not None
