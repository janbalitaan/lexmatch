"""The threshold."""

from __future__ import annotations

from typing import ClassVar

import pytest

from lexmatch import Entry, Index
from lexmatch.exceptions import TuningError
from lexmatch.models.tuning import Tuning
from tests.tuning.scoring_is_tunable import ENTRIES


class TestTheThreshold:
    # A weak but non-zero match. What counts as weak has changed twice:
    # "can I work remotely" stopped being weak when typo correction read
    # "remotely" as "remote", and "the next thing" stopped being weak when
    # BM25 gained a reachable ceiling. Weak now means a *low-IDF* word —
    # one appearing in several entries, which specificity scales down — so
    # the fixture below has "work" in all three.
    WEAK = "you work"
    WEAK_ENTRIES: ClassVar[list[Entry]] = [
        Entry(question="Are you open to remote work?", answer="Yes.", aliases=["remote"]),
        Entry(
            question="Can you start work next month?", answer="Yes.", aliases=["availability"]
        ),
        Entry(question="Do you enjoy the work?", answer="Yes.", aliases=["enjoyment"]),
    ]

    def test_raising_it_refuses_a_weak_match(self):
        entry, score = Index(self.WEAK_ENTRIES, threshold=0.9).answer(self.WEAK)
        assert 0 < score < 0.9, f"{self.WEAK!r} scored {score:.3f}, not weak"
        assert entry is None

    def test_a_low_threshold_accepts_it(self):
        entry, score = Index(self.WEAK_ENTRIES, threshold=0.1).answer(self.WEAK)
        assert score >= 0.1
        assert entry is not None

    def test_above_one_refuses_everything(self):
        """Scores cap at 1.0, so this is the honest way to turn answering
        off without taking the index apart."""
        assert Index(ENTRIES, threshold=1.01).answer("remote")[0] is None

    def test_an_explicit_threshold_wins_over_the_tuning(self):
        """A caller who named it meant it."""
        index = Index(self.WEAK_ENTRIES, threshold=0.9, tuning=Tuning(threshold=0.1))
        assert index.threshold == 0.9
        assert index.answer(self.WEAK)[0] is None

    def test_a_negative_threshold_is_refused(self):
        with pytest.raises(TuningError, match="cannot be negative"):
            Tuning(threshold=-0.1)
