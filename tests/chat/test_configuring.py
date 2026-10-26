"""Configuring."""

from __future__ import annotations

import pytest

from lexmatch import Corrections, Index, Tuning
from lexmatch.exceptions import TuningError
from tests.chat.typos_are_read import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestConfiguring:
    def test_it_can_be_turned_off(self):
        off = Index(ENTRIES, tuning=Tuning().with_corrections(enabled=False))
        assert off.answer("pricng")[0] is None
        assert Index(ENTRIES).answer("pricng")[0] is not None

    def test_the_bar_can_be_raised(self):
        strict = Corrections(similarity=0.99)
        assert strict._best("remte", frozenset({"remote"})) == "remte"

    def test_the_minimum_length_can_be_raised(self):
        longer = Corrections(minimum_length=10)
        assert longer._best("remte", frozenset({"remote"})) == "remte"

    def test_an_empty_vocabulary_changes_nothing(self):
        assert Corrections().apply(["remte"], frozenset()) == ["remte"]

    @pytest.mark.parametrize("similarity", [0.0, -0.1, 1.5])
    def test_a_nonsense_similarity_is_refused(self, similarity):
        with pytest.raises(TuningError, match="similarity"):
            Corrections(similarity=similarity)

    def test_a_zero_minimum_length_is_refused(self):
        with pytest.raises(TuningError, match="at least 1"):
            Corrections(minimum_length=0)

    def test_describe_says_when_it_is_off(self):
        assert "off" in Corrections(enabled=False).describe()

    def test_describe_names_the_settings_when_on(self):
        described = Corrections().describe()
        assert "0.8" in described
        assert "4 characters" in described
