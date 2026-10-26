"""An unanswered social message is still honest."""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index, Outcome, SmallTalk
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


class TestAnUnansweredSocialMessageIsStillHonest:
    def test_an_uncovered_question_with_a_social_word_is_refused(self, index):
        reply = index.reply("good afternoon, do you know kubernetes")
        assert reply.outcome is not Outcome.ANSWERED or reply.entry.answer != "Hello."
