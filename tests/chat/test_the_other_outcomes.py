"""The other outcomes."""

from __future__ import annotations

import pytest

from lexmatch import Composer, Index
from tests.chat.composing_a_reply import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestTheOtherOutcomes:
    def test_ambiguity_asks_which(self, index):
        said = index.respond("what is your rate")
        assert said.startswith("Which did you mean")
        assert "design" in said
        assert "review" in said

    def test_the_options_lose_their_question_marks(self, index):
        """Or the sentence ends in "??"."""
        assert "??" not in index.respond("what is your rate")

    def test_a_negative_question_is_hedged(self, index):
        said = index.respond("are you not open to remote work")
        assert "rephrase" in said
        assert "Yes" not in said, "it must not answer the opposite"

    def test_nothing_matched_offers_suggestions(self, index):
        said = index.respond("what is the weather")
        assert "don't have an answer" in said
        assert "You could try" in said

    def test_an_empty_index_says_so_without_suggestions(self):
        assert Index([]).respond("anything") == Composer.NOTHING
