"""`stem` is pure and called on every token of every entry and query, so
it is memoized. The cache has to be dropped when the rules change."""

from __future__ import annotations

from lexmatch.stemming import Stemmer


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
