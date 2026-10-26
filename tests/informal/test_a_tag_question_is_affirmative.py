""" "you've led teams before, haven't you?" expects "yes".

Five of twenty informally written questions were tag questions, and all
five matched perfectly and were then thrown away as negative."""

from __future__ import annotations

import pytest

from lexmatch import Index, Outcome
from lexmatch.negation import Negation
from tests.informal.how_people_actually_type import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestATagQuestionIsAffirmative:
    """ "you've led teams before, haven't you?" expects "yes".

    Five of twenty informally written questions were tag questions, and all
    five matched perfectly and were then thrown away as negative.
    """

    @pytest.mark.parametrize(
        "message",
        [
            "youve led teams before havent you",
            "youre open to remote arent you",
            "thats a lot of years isnt it",
            "you do consulting dont you",
            "that works doesnt it",
            "you can start soon cant you",
        ],
    )
    def test_it_is_not_read_as_negative(self, message):
        assert not Negation.present_in(message), message

    def test_the_answer_survives(self, index):
        reply = index.reply("youve led teams before havent you")
        assert reply.outcome is Outcome.ANSWERED
        assert reply.entry.answer == "LEADERSHIP"

    def test_a_negative_question_is_still_negative(self):
        """The tag has to be at the end. A negation at the front is a
        genuine negative question."""
        assert Negation.present_in("arent you open to remote work")
        assert Negation.present_in("havent you got any availability at all")
