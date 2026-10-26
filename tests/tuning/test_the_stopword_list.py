"""The stopword list."""

from __future__ import annotations

from lexmatch import Index
from lexmatch.models.tuning import Tuning
from tests.tuning.scoring_is_tunable import ENTRIES


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
