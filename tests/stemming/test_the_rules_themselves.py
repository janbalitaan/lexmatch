"""The rules themselves."""

from __future__ import annotations

from lexmatch.stemming import Stemmer


class TestTheRulesThemselves:
    def test_a_doubled_consonant_collapses(self):
        """ "running" reaches "run" rather than "runn"."""
        assert Stemmer.stem("running") == Stemmer.stem("run")

    def test_a_double_that_belongs_is_kept(self):
        assert Stemmer.stem("stall").endswith("ll")

    def test_a_short_word_is_untouched(self):
        for word in ("is", "as", "do", "go", "ask"):
            assert Stemmer.stem(word) == word

    def test_a_word_with_no_vowel_is_untouched(self):
        assert Stemmer.stem("xyz") == "xyz"

    def test_a_rule_that_would_leave_a_stub_is_skipped(self):
        """ "ties" does not become "ty", because the rule's floor stops it."""
        assert len(Stemmer.stem("ties")) >= 3

    def test_stem_all_keeps_order_and_count(self):
        words = ["consulting", "rates", "process", "built"]
        stems = Stemmer.stem_all(words)
        assert len(stems) == len(words)
        assert stems[0] == Stemmer.stem("consulting")
        assert stems[-1] == "build"

    def test_the_suffix_table_is_replaceable(self):
        assert isinstance(Stemmer.SUFFIXES, tuple)
        assert any(ending == "ing" for ending, _, _ in Stemmer.SUFFIXES)
