"""Folding a word's inflections onto one token.

What matters is not that a stem looks like a word — it never has to, because
a stem is never shown to anyone. What matters is that every inflection of one
word reaches the *same* token, and that two different words do not.
"""

from __future__ import annotations

import pytest

from lexmatch.stemming import Stemmer


class TestEveryInflectionReachesOneStem:
    @pytest.mark.parametrize(
        "forms",
        [
            ("consult", "consults", "consulting", "consulted"),
            ("scale", "scales", "scaling", "scaled"),
            ("manage", "manages", "managing", "managed"),
            ("experience", "experiences", "experienced"),
            ("design", "designs", "designing", "designed"),
            ("mentor", "mentors", "mentoring", "mentored"),
            ("pair", "pairs", "pairing", "paired"),
            ("measure", "measures", "measuring", "measured"),
            ("deploy", "deploys", "deploying", "deployed"),
            ("rate", "rates"),
            ("policy", "policies"),
            ("remote", "remotely"),
        ],
    )
    def test_they_agree(self, forms):
        stems = {Stemmer.stem(form) for form in forms}
        assert len(stems) == 1, f"{forms} split into {sorted(stems)}"


class TestIrregularFormsAreMapped:
    """No suffix rule reaches these, so they are listed."""

    @pytest.mark.parametrize(
        ("inflected", "base"),
        [
            ("built", "build"),
            ("bought", "buy"),
            ("led", "lead"),
            ("made", "make"),
            ("paid", "pay"),
            ("written", "write"),
            ("found", "find"),
            ("people", "person"),
            ("children", "child"),
            ("analyses", "analysis"),
        ],
    )
    def test_the_base_is_reached(self, inflected, base):
        assert Stemmer.stem(inflected) == Stemmer.stem(base)

    def test_the_mapping_is_replaceable(self):
        """Stated in the class docstring, so it is tested."""
        assert Stemmer.IRREGULAR["built"] == "build"
        assert isinstance(Stemmer.IRREGULAR, dict)


class TestDifferentWordsStayDifferent:
    """The reason this is not a Porter stemmer.

    Porter strips derivational endings too, which merges words that mean
    different things — "university" and "universe" both become "univers".
    """

    @pytest.mark.parametrize(
        ("left", "right"),
        [
            ("university", "universe"),
            ("business", "busy"),
            ("process", "profess"),
            ("training", "train"),
            ("meeting", "meet"),
            ("note", "not"),
            ("rate", "rat"),
            ("code", "cod"),
            ("payment", "pay"),
            ("consultant", "consult"),
        ],
    )
    def test_they_do_not_collide(self, left, right):
        assert Stemmer.stem(left) != Stemmer.stem(right)


class TestWordsARuleWouldDamage:
    @pytest.mark.parametrize(
        "word",
        [
            "process",
            "business",
            "status",
            "kubernetes",
            "css",
            "aws",
            "series",
            "always",
            "only",
            "class",
            "across",
        ],
    )
    def test_they_are_left_alone(self, word):
        assert Stemmer.stem(word) == word

    def test_the_keep_set_is_replaceable(self):
        assert "process" in Stemmer.KEEP
        assert isinstance(Stemmer.KEEP, frozenset)


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


class TestTheMemo:
    """`stem` is pure and called on every token of every entry and query, so
    it is memoized. The cache has to be dropped when the rules change."""

    def test_the_same_word_gives_the_same_answer(self):
        assert Stemmer.stem("consulting") == Stemmer.stem("consulting")

    def test_forget_drops_it(self):
        original = dict(Stemmer.IRREGULAR)
        try:
            assert Stemmer.stem("flurbed") == "flurb"
            Stemmer.IRREGULAR = {**original, "flurbed": "flurgle"}
            Stemmer.forget()
            assert Stemmer.stem("flurbed") == Stemmer.stem("flurgle")
        finally:
            Stemmer.IRREGULAR = original
            Stemmer.forget()

    def test_the_rules_are_back_after_the_test(self):
        assert Stemmer.stem("built") == "build"
