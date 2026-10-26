"""A clear match."""

from __future__ import annotations

import pytest

from lexmatch import Index, Outcome
from tests.chat.a_chatbot_turn import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestAClearMatch:
    def test_it_is_answered(self, index):
        reply = index.reply("design rate")
        assert reply.outcome is Outcome.ANSWERED
        assert reply.answered

    def test_the_text_is_the_answer(self, index):
        assert index.reply("design rate").text == "£600/day for design."

    def test_there_are_no_alternatives(self, index):
        assert index.reply("design rate").alternatives == ()

    def test_the_score_is_carried(self, index):
        assert index.reply("design rate").score > 0.9
