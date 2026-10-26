""" "Can't you start sooner?" asks for the notice period."""

from __future__ import annotations

import pytest

from lexmatch import Index
from lexmatch.negation import Negation
from tests.informal.how_people_actually_type import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestAPoliteRequestIsAffirmative:
    """ "Can't you start sooner?" asks for the notice period."""

    @pytest.mark.parametrize(
        "message",
        ["cant you start sooner", "couldnt you reduce the cost", "wouldnt you consider remote"],
    )
    def test_it_is_not_read_as_negative(self, message):
        assert not Negation.present_in(message), message

    def test_the_answer_survives(self, index):
        assert index.reply("couldnt you reduce the cost").entry.answer == "COST"

    def test_only_at_the_start(self):
        """ "we can't afford that rate" is a genuine negative."""
        assert Negation.present_in("we cant afford that rate")
