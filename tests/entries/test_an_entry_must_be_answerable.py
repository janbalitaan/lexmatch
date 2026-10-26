"""An entry that could never match anything is refused when it is built.

Not left to fail at match time, because the two are indistinguishable
afterwards: an entry with a blank question scores zero against every query,
exactly as an entry about something nobody asks does. One is a broken
question set and the other is normal.

Question sets are generated as often as they are written — a spreadsheet
export, a content system, a CV parser — and a blank row is the ordinary
failure of all three.
"""

from __future__ import annotations

import pytest

from lexmatch import Entry, EntryError, LexmatchError
from lexmatch.utils.text import Tokenizer


class TestAMissingQuestionIsRefused:
    @pytest.mark.parametrize("question", ["", "   ", "\n", "\t "])
    def test_blank_in_any_form(self, question):
        with pytest.raises(EntryError, match="needs a question"):
            Entry(question=question, answer="An answer.")

    def test_the_message_shows_the_answer_so_the_row_can_be_found(self):
        with pytest.raises(EntryError, match="Use the Forgot password"):
            Entry(question="", answer="Use the Forgot password link.")


class TestAMissingAnswerIsRefused:
    @pytest.mark.parametrize("answer", ["", "   ", "\n"])
    def test_blank_in_any_form(self, answer):
        with pytest.raises(EntryError, match="needs an answer"):
            Entry(question="What do you do?", answer=answer)

    def test_the_message_shows_the_question(self):
        with pytest.raises(EntryError, match="What do you do"):
            Entry(question="What do you do?", answer="")


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


class TestWhatIsForgivenInstead:
    """An alias is optional by nature, so a blank one is dropped rather than
    refused — a trailing empty column is what a spreadsheet export looks
    like, and dropping one costs nothing."""

    def test_blank_aliases_are_dropped(self):
        entry = Entry(question="What do you do?", answer="A.", aliases=["", "  ", "job"])
        assert entry.aliases == ["job"]

    def test_blank_tags_are_dropped(self):
        entry = Entry(question="What do you do?", answer="A.", tags=["", "work"])
        assert entry.tags == ["work"]

    def test_an_entry_of_only_blank_aliases_still_builds(self):
        entry = Entry(question="What do you do?", answer="A.", aliases=["", ""])
        assert entry.aliases == []


class TestAValidEntryIsUntouched:
    def test_it_builds(self):
        entry = Entry(
            question="Are you open to remote work?",
            answer="Yes.",
            aliases=["remote"],
            tags=["logistics"],
        )
        assert entry.question == "Are you open to remote work?"
        assert entry.aliases == ["remote"]
        assert entry.tags == ["logistics"]

    def test_the_error_is_a_lexmatch_error(self):
        """So one `except` catches everything from this library."""
        assert issubclass(EntryError, LexmatchError)
