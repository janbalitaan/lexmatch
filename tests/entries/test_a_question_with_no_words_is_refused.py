""" "???" normalizes to nothing, so no query could reach it."""

from __future__ import annotations

import pytest

from lexmatch import Entry, EntryError
from lexmatch.utils.text import Tokenizer


class TestAQuestionWithNoWordsIsRefused:
    """ "???" normalizes to nothing, so no query could reach it."""

    @pytest.mark.parametrize("question", ["???", "...", "!!!", "- -"])
    def test_punctuation_only(self, question):
        with pytest.raises(EntryError, match="leaves no tokens"):
            Entry(question=question, answer="An answer.")

    def test_the_message_names_the_cause(self):
        """Single characters are dropped, which is why "C" is unmatchable."""
        with pytest.raises(EntryError, match="SHORTEST_WORD"):
            Entry(question="C", answer="A language.")

    def test_lowering_the_minimum_makes_it_answerable(self):
        """So the refusal is a consequence of a setting, not a dead end."""
        original = Tokenizer.SHORTEST_WORD
        try:
            Tokenizer.SHORTEST_WORD = 1
            entry = Entry(question="C", answer="A language.")
            assert entry.question == "C"
        finally:
            Tokenizer.SHORTEST_WORD = original
