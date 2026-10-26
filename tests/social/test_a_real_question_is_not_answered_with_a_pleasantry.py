"""A real question is not answered with a pleasantry."""

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


class TestARealQuestionIsNotAnsweredWithAPleasantry:
    @pytest.mark.parametrize(
        ("message", "expected"),
        [
            ("is the pay good", "RATE"),
            ("do you care about the frontend at all", "FRONTEND"),
            ("hi do you do consulting", "CONSULTING"),
        ],
    )
    def test_the_subject_wins_over_the_social_word(self, index, message, expected):
        reply = index.reply(message)
        assert reply.answered, f"{message!r} was refused"
        assert reply.entry.answer == expected

    def test_a_greeting_prefix_does_not_swallow_the_question(self, index):
        """ "hi" is a greeting phrasing, "consulting" is not, so the greeting
        entry is out and the consulting entry is free to win."""
        assert index.reply("hi do you do consulting").entry.answer == "CONSULTING"
