"""A word in the vocabulary is better evidence than any similarity."""

from __future__ import annotations

import pytest

from lexmatch import Corrections, Index
from tests.chat.typos_are_read import ENTRIES, VOCABULARY


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestItNeverOverridesARealWord:
    """A word in the vocabulary is better evidence than any similarity."""

    @pytest.mark.parametrize("word", ["senior", "junior", "rust", "python", "remote"])
    def test_a_vocabulary_word_is_untouched(self, word):
        assert Corrections()._best(word, VOCABULARY) == word

    def test_an_unrelated_query_still_refuses(self, index):
        """Correction must not invent a match out of nothing."""
        for query in ("what is the weather", "who won the match", "xyzzy plugh"):
            assert index.answer(query)[0] is None, query
