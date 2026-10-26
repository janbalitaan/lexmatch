"""Every number the scorer uses, changeable without editing the package.

The four were constants read straight out of the module, so a domain the
defaults suit badly had no recourse. One of them was worse than unreachable:
`MIN_CONTENT_OVERLAP` was exported, documented and never read — the scorer
hard-coded "any overlap at all", so a caller who raised it got no change and
no error.
"""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index
from lexmatch.constants import (
    DEFAULT_THRESHOLD,
    LENGTH_PENALTY,
    MIN_CONTENT_OVERLAP,
    TERM_FREQUENCY_SATURATION,
)
from lexmatch.exceptions import TuningError
from lexmatch.models.tuning import Tuning
from lexmatch.stopwords import STOPWORDS

ENTRIES = [
    Entry(question="Are you open to remote work?", answer="Yes.", aliases=["remote"]),
    Entry(question="Can you start next month?", answer="Yes.", aliases=["availability"]),
]

# Four entries sharing one content word dilute its IDF, so BM25 stays low
# while the phrase scorer can still win on shared filler — which is where
# the overlap guard decides the outcome rather than being masked by BM25.
DILUTED = [
    Entry(question="What is your rate for design work?", answer="A.", aliases=[]),
    Entry(question="What is your rate for review work?", answer="B.", aliases=[]),
    Entry(question="What is your rate for audit work?", answer="C.", aliases=[]),
    Entry(question="What is your rate for training work?", answer="D.", aliases=[]),
]


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


class TestTheThreshold:
    # A weak but non-zero match, scoring 0.485 against this index. The
    # earlier choice of "can I work remotely" stopped being weak once typo
    # correction began reading "remotely" as "remote" and lifting it to
    # 1.000 — which is the correction working, and makes it useless here.
    WEAK = "the next thing"

    def test_raising_it_refuses_a_weak_match(self):
        entry, score = Index(ENTRIES, threshold=0.9).answer(self.WEAK)
        assert 0 < score < 0.9, f"{self.WEAK!r} scored {score:.3f}, not weak"
        assert entry is None

    def test_the_default_accepts_it(self):
        entry, score = Index(ENTRIES).answer(self.WEAK)
        assert score >= Index(ENTRIES).threshold
        assert entry is not None

    def test_above_one_refuses_everything(self):
        """Scores cap at 1.0, so this is the honest way to turn answering
        off without taking the index apart."""
        assert Index(ENTRIES, threshold=1.01).answer("remote")[0] is None

    def test_an_explicit_threshold_wins_over_the_tuning(self):
        """A caller who named it meant it."""
        index = Index(ENTRIES, threshold=0.9, tuning=Tuning(threshold=0.1))
        assert index.threshold == 0.9
        assert index.answer(self.WEAK)[0] is None

    def test_a_negative_threshold_is_refused(self):
        with pytest.raises(TuningError, match="cannot be negative"):
            Tuning(threshold=-0.1)


class TestTheOverlapGuardIsNowRead:
    """It was exported, documented and dead."""

    def test_raising_it_turns_a_confident_match_into_a_refusal(self):
        query = "what is your rate for consulting"
        loose = Index(DILUTED, tuning=Tuning(minimum_overlap=1))
        strict = Index(DILUTED, tuning=Tuning(minimum_overlap=2))
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
        asked = {"notice", "of", "termination"}
        content = asked - loose.tuning.stopwords
        assert loose._phrase_score(0, asked, content) > 0
        assert strict._phrase_score(0, asked, content) == 0

    def test_zero_lets_a_query_match_on_filler(self):
        index = Index(DILUTED, tuning=Tuning(minimum_overlap=0))
        assert index.score("what is your")[0][0] > 0

    def test_a_negative_overlap_is_refused(self):
        with pytest.raises(TuningError, match="cannot be negative"):
            Tuning(minimum_overlap=-1)


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


class TestTheStopwordList:
    def test_extra_words_are_added(self):
        tuning = Tuning().with_stopwords(extra=["please", "kindly"])
        assert "please" in tuning.stopwords
        assert "kindly" in tuning.stopwords

    def test_the_shipped_words_are_kept_when_adding(self):
        tuning = Tuning().with_stopwords(extra=["please"])
        assert "what" in tuning.stopwords

    def test_a_word_can_be_taken_out(self):
        """For a domain where a stopword is content: "can" is also a tin,
        "will" is also a legal document."""
        assert "can" in Tuning().stopwords
        assert "can" not in Tuning().with_stopwords(keep=["can"]).stopwords

    def test_the_list_can_be_replaced_outright(self):
        """For another language."""
        tuning = Tuning().with_stopwords(["el", "la", "de"])
        assert tuning.stopwords == frozenset({"el", "la", "de"})
        assert "what" not in tuning.stopwords

    def test_keep_wins_over_extra(self):
        """Asking to keep a word is the more specific instruction."""
        tuning = Tuning().with_stopwords(extra=["rate"], keep=["rate"])
        assert "rate" not in tuning.stopwords

    def test_words_are_lower_cased(self):
        """Matching happens on normalized tokens, so a capitalized entry
        would look like it worked while matching nothing."""
        assert "please" in Tuning().with_stopwords(extra=["PLEASE"]).stopwords

    def test_the_scorer_uses_the_tuning_list(self):
        index = Index(ENTRIES, tuning=Tuning().with_stopwords(["xyzzy"]))
        assert index.tuning.stopwords == frozenset({"xyzzy"})
        assert "what" not in index.tuning.stopwords


class TestDescribe:
    def test_it_names_every_number(self):
        described = Tuning().describe()
        for part in ("threshold", "saturation", "length penalty", "minimum overlap"):
            assert part in described

    def test_it_counts_the_stopwords(self):
        described = Tuning().with_stopwords(["a", "b"]).describe()
        assert "2 stopwords" in described

    def test_it_does_not_list_them(self):
        """Safe to log: seventy-seven words in a log line is noise."""
        assert "what" not in Tuning().describe()
