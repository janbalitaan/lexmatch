"""Saturation and length penalty."""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index
from lexmatch.exceptions import TuningError
from lexmatch.models.tuning import Tuning
from tests.tuning.scoring_is_tunable import ENTRIES


class TestSaturationAndLengthPenalty:
    def test_saturation_changes_the_scores(self):
        low = Index(ENTRIES, tuning=Tuning(saturation=0.5))
        high = Index(ENTRIES, tuning=Tuning(saturation=4.0))
        assert low.score("remote work")[0][0] != high.score("remote work")[0][0]

    def test_zero_saturation_is_refused(self):
        """It divides by zero in the term-frequency term."""
        with pytest.raises(TuningError, match="above 0"):
            Tuning(saturation=0)

    def test_a_length_penalty_of_zero_ignores_entry_length(self):
        """Two entries differing only in length should then score alike."""
        entries = [
            Entry(question="remote work", answer="A.", aliases=[]),
            Entry(
                question="remote work and also several other unrelated topics here",
                answer="B.",
                aliases=[],
            ),
        ]
        ignored = Index(entries, tuning=Tuning(length_penalty=0.0))
        applied = Index(entries, tuning=Tuning(length_penalty=1.0))
        gap_ignored = abs(ignored.score("remote")[0][0] - ignored.score("remote")[1][0])
        gap_applied = abs(applied.score("remote")[0][0] - applied.score("remote")[1][0])
        assert gap_ignored <= gap_applied

    @pytest.mark.parametrize("value", [-0.1, 1.1, 2.0])
    def test_a_length_penalty_outside_zero_to_one_is_refused(self, value):
        with pytest.raises(TuningError, match="between 0 and 1"):
            Tuning(length_penalty=value)
