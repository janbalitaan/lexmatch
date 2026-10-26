"""The guards."""

from __future__ import annotations

import pytest

from lexmatch import Corrections, Index
from tests.chat.typos_are_read import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestTheGuards:
    def test_a_short_token_is_skipped(self):
        """Below four characters almost everything is one edit from
        everything, so "api" would correct to "and"."""
        assert Corrections()._best("api", frozenset({"and", "all"})) == "api"

    def test_the_similarity_bar_holds(self):
        """`rateing` is 0.667 similar to `rates`, under the 0.8 bar."""
        assert Corrections()._best("rateing", frozenset({"rates"})) == "rateing"

    def test_a_tie_is_left_alone(self):
        """Two equally close candidates means the word is ambiguous."""
        assert Corrections()._best("bat", frozenset({"cat", "rat"})) == "bat"

    def test_a_clear_winner_is_taken(self):
        assert Corrections()._best("desgin", frozenset({"design", "review"})) == "design"

    def test_length_spread_limits_the_candidates(self):
        """A token cannot be a typo of something far longer."""
        assert Corrections()._best("rate", frozenset({"rationalisation"})) == "rate"
