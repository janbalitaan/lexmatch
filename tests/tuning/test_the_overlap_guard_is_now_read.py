"""It was exported, documented and dead."""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index
from lexmatch.exceptions import TuningError
from lexmatch.models.tuning import Tuning
from lexmatch.stemming import Stemmer
from tests.tuning.scoring_is_tunable import DILUTED


class TestTheOverlapGuardIsNowRead:
    """It was exported, documented and dead."""

    def test_raising_it_turns_a_confident_match_into_a_refusal(self):
        query = "what is your rate for consulting"
        # 0.446 with the guard at 1, which is a hair under the 0.45 default
        # now that phrase overlap is IDF-weighted. The threshold is lowered
        # so this test turns on the guard rather than on the threshold.
        # 0.139 with the guard at 1 and 0.084 at 2, both low because every
        # word these entries share is in all of them. The threshold is set
        # between the two so the guard is what decides.
        loose = Index(DILUTED, tuning=Tuning(minimum_overlap=1), threshold=0.1)
        strict = Index(DILUTED, tuning=Tuning(minimum_overlap=2), threshold=0.1)
        assert loose.answer(query)[0] is not None
        assert strict.answer(query)[0] is None

    def test_it_changes_the_phrase_score_directly(self):
        """Where the guard lives. Through `score()` it is often masked by
        BM25 winning the maximum, which is why the unit is checked too."""
        entries = [
            Entry(
                question="What is your notice period and start date?",
                answer="One month.",
                aliases=[],
            )
        ]
        loose = Index(entries, tuning=Tuning(minimum_overlap=1))
        strict = Index(entries, tuning=Tuning(minimum_overlap=2))
        # `score` prepares these once per query; the unit takes them ready
        # so the guard can be exercised without the whole pass.
        # Stemmed by hand, because the index stems what it holds and these
        # are being handed straight to the scorer: "notice" is "notic" there.
        # One shared content word, which is what the guard counts. "start"
        # would share a second and make both settings pass.
        asked = set(Stemmer.stem_all(["notice", "of", "termination"]))
        # The folded stopword set, because the tokens above are folded too.
        content = asked - loose._stopwords
        assert loose._phrase_score(0, asked, content, asked) > 0
        assert strict._phrase_score(0, asked, content, asked) == 0

    def test_zero_lets_a_query_match_on_filler(self):
        index = Index(DILUTED, tuning=Tuning(minimum_overlap=0))
        assert index.score("what is your")[0][0] > 0

    def test_a_negative_overlap_is_refused(self):
        with pytest.raises(TuningError, match="cannot be negative"):
            Tuning(minimum_overlap=-1)
