"""Adopting `Tuning` has to be invisible until a caller asks otherwise."""

from __future__ import annotations

from lexmatch import Index
from lexmatch.constants import (
    DEFAULT_THRESHOLD,
    LENGTH_PENALTY,
    MIN_CONTENT_OVERLAP,
    TERM_FREQUENCY_SATURATION,
)
from lexmatch.models.tuning import Tuning
from lexmatch.stopwords import STOPWORDS
from tests.tuning.scoring_is_tunable import ENTRIES


class TestTheDefaultsChangeNothing:
    """Adopting `Tuning` has to be invisible until a caller asks otherwise."""

    def test_an_index_without_tuning_uses_the_constants(self):
        tuning = Index(ENTRIES).tuning
        assert tuning.threshold == DEFAULT_THRESHOLD
        assert tuning.saturation == TERM_FREQUENCY_SATURATION
        assert tuning.length_penalty == LENGTH_PENALTY
        assert tuning.minimum_overlap == MIN_CONTENT_OVERLAP

    def test_the_stopwords_are_the_shipped_ones(self):
        assert Index(ENTRIES).tuning.stopwords == STOPWORDS

    def test_scores_are_unchanged_by_passing_an_empty_tuning(self):
        plain = Index(ENTRIES).score("can I work remotely")
        tuned = Index(ENTRIES, tuning=Tuning()).score("can I work remotely")
        assert [value for value, _ in plain] == [value for value, _ in tuned]
