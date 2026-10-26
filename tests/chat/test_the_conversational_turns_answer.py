"""The conversational turns answer."""

from __future__ import annotations

import pytest

from lexmatch import Index, SmallTalk
from tests.chat.small_talk import CONTENT, REPLIES


@pytest.fixture
def index() -> Index:
    return Index([*SmallTalk.entries(REPLIES), *CONTENT])


class TestTheConversationalTurnsAnswer:
    @pytest.mark.parametrize(
        ("message", "expected"),
        [
            ("hi", "greeting"),
            ("hello", "greeting"),
            ("hey there", "greeting"),
            ("good morning", "greeting"),
            ("thanks", "thanks"),
            ("thanks!", "thanks"),
            ("cheers", "thanks"),
            ("much appreciated", "thanks"),
            ("bye", "farewell"),
            ("take care", "farewell"),
            ("who are you", "identity"),
            ("are you a bot", "identity"),
            ("are you human", "identity"),
            ("what can i ask", "capability"),
            ("help", "capability"),
            ("how are you", "wellbeing"),
        ],
    )
    def test_it_reaches_the_right_intent(self, index, message, expected):
        entry, score = index.answer(message)
        assert entry is not None, f"{message!r} refused at {score:.3f}"
        assert entry.answer == REPLIES[expected], f"{message!r} -> {entry.answer!r}"

    def test_content_questions_still_work(self, index):
        """Small talk must not crowd out the real entries."""
        assert index.answer("remote?")[0].answer == "Yes."
        assert index.answer("pricing")[0].answer == "It depends."

    def test_an_unrelated_question_is_still_refused(self, index):
        """Adding small talk must not make the index answer everything."""
        assert index.answer("what is the weather")[0] is None
