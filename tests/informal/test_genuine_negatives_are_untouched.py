"""Genuine negatives are untouched."""

from __future__ import annotations

import pytest

from lexmatch import Index, Outcome
from lexmatch.negation import Negation
from tests.informal.how_people_actually_type import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestGenuineNegativesAreUntouched:
    @pytest.mark.parametrize(
        "message",
        [
            "are you not open to remote work",
            "you dont do consulting",
            "i dont need visa sponsorship",
            "isnt there any flexibility",
            "you never worked remotely",
            "no longer available",
        ],
    )
    def test_they_stay_negative(self, message):
        assert Negation.present_in(message), message

    def test_a_negative_query_is_reported_as_such(self, index):
        assert index.reply("are you not open to remote work").outcome is Outcome.NEGATED

    def test_the_patterns_are_replaceable(self):
        assert Negation._TAG_QUESTION.pattern
        assert Negation._POLITE_REQUEST.pattern
