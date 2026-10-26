""" "great, thanks" is one unit, because a comma is not a terminator."""

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


class TestAnAcknowledgementIsNotASubject:
    """ "great, thanks" is one unit, because a comma is not a terminator."""

    def test_it_does_not_suppress_the_small_talk(self, index):
        assert index.reply("great, thanks!").entry.answer == "You're welcome."

    def test_nothing_is_reported_as_unanswered(self, index):
        """The defect this fixed: a wholly correct reply counted as partial."""
        assert index.unanswered("great, thanks!") == []

    @pytest.mark.parametrize("message", ["ok thanks", "cool, cheers", "right, bye"])
    def test_other_acknowledgements_behave_the_same(self, index, message):
        assert index.reply(message).answered

    def test_a_substantive_word_still_suppresses(self, index):
        """ "good" is an acknowledgement and "pay" is not, so "pay" decides."""
        assert index.reply("is the pay good").entry.answer == "RATE"
