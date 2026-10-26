"""Small talk itself still works."""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index, SmallTalk
from tests.social.small_talk_stays_in_its_lane import REPLIES


@pytest.fixture
def index() -> Index:
    return Index(
        [
            *SmallTalk.entries(REPLIES),
            Entry(
                question="What are your rate expectations?",
                answer="RATE",
                aliases=["rate", "pay", "salary"],
            ),
            Entry(
                question="Do you work on the frontend?",
                answer="FRONTEND",
                aliases=["frontend", "ui work"],
            ),
            Entry(
                question="Do you do consulting?",
                answer="CONSULTING",
                aliases=["consulting", "advisory"],
            ),
        ]
    )


class TestSmallTalkItselfStillWorks:
    @pytest.mark.parametrize(
        ("message", "expected"),
        [
            ("hello", "Hello."),
            ("yo", "Hello."),
            ("good morning", "Hello."),
            ("thanks", "You're welcome."),
            ("cheers", "You're welcome."),
            ("bye", "Take care."),
            ("take care", "Take care."),
            ("who are you", "I'm a bot."),
            ("how are you", "Well, thanks."),
        ],
    )
    def test_it_is_answered(self, index, message, expected):
        reply = index.reply(message)
        assert reply.answered, f"{message!r} was refused"
        assert reply.entry.answer == expected
