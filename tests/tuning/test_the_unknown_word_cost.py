"""Off by default, and measured twice before it was left off.

An unknown word has no inverse document frequency, so it contributes
nothing to the score ceiling and is invisible — which leaves a query
satisfiable by matching only the words it happened to share. Charging
for it nonetheless made the library worse across 133 measured questions,
because in a question set small enough to hand write, most words in a
naturally phrased question are absent from every entry."""

from __future__ import annotations

from typing import ClassVar

import pytest

from lexmatch import Entry, Index
from lexmatch.exceptions import TuningError
from lexmatch.models.tuning import Tuning


class TestTheUnknownWordCost:
    """Off by default, and measured twice before it was left off.

    An unknown word has no inverse document frequency, so it contributes
    nothing to the score ceiling and is invisible — which leaves a query
    satisfiable by matching only the words it happened to share. Charging
    for it nonetheless made the library worse across 133 measured questions,
    because in a question set small enough to hand write, most words in a
    naturally phrased question are absent from every entry.
    """

    SPARSE: ClassVar[list[Entry]] = [
        Entry(question="Are you open to remote work?", answer="REMOTE", aliases=["remote"]),
        Entry(question="What is your notice period?", answer="NOTICE", aliases=["notice"]),
        Entry(question="What are your rates?", answer="RATE", aliases=["rate"]),
    ]
    #: One known content word, one the index has never seen.
    HALF_KNOWN = "do you like working alone"

    def test_it_is_off_by_default(self):
        assert Tuning().unknown_word_cost == 0.0

    def test_off_the_query_is_answered_on_its_known_word(self):
        """The documented cost of leaving it off."""
        assert Index(self.SPARSE).reply(self.HALF_KNOWN).answered

    def test_raising_it_lowers_the_score(self):
        loose = Index(self.SPARSE)
        strict = Index(self.SPARSE, tuning=Tuning(unknown_word_cost=1.0))
        assert strict.score(self.HALF_KNOWN)[0][0] < loose.score(self.HALF_KNOWN)[0][0]

    def test_a_fully_recognized_query_is_unaffected(self):
        loose = Index(self.SPARSE)
        strict = Index(self.SPARSE, tuning=Tuning(unknown_word_cost=1.0))
        for query in ("remote work", "notice period", "rate"):
            assert strict.score(query)[0][0] == loose.score(query)[0][0], query

    def test_a_cost_outside_zero_to_one_is_refused(self):
        with pytest.raises(TuningError, match="between 0 and 1"):
            Tuning(unknown_word_cost=1.5)
