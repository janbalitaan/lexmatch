"""The reply itself."""

from __future__ import annotations

import pytest

from lexmatch import Index, Outcome, Reply
from tests.chat.a_chatbot_turn import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestTheReplyItself:
    def test_describe_carries_the_shape(self, index):
        described = index.reply("what is your rate").describe()
        assert "ambiguous" in described
        assert "2 alternatives" in described

    def test_describe_holds_no_question_or_answer_text(self, index):
        """A log of what visitors asked is personal data, and its retention
        should be deliberate rather than a side effect of debugging."""
        described = index.reply("design rate").describe()
        assert "design rate" not in described
        assert "£600" not in described

    def test_a_bare_reply_is_unanswered(self):
        assert not Reply(outcome=Outcome.UNANSWERED).answered

    def test_the_outcome_serializes_as_its_name(self):
        """It ends up in JSON more often than not."""
        assert Outcome.AMBIGUOUS == "ambiguous"
        assert f"{Outcome.ANSWERED.value}" == "answered"
