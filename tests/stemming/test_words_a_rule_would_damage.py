"""Words a rule would damage."""

from __future__ import annotations

import pytest

from lexmatch.stemming import Stemmer


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
