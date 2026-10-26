"""A missing question is refused."""

from __future__ import annotations

import pytest

from lexmatch import Entry, EntryError


class TestAMissingQuestionIsRefused:
    @pytest.mark.parametrize("question", ["", "   ", "\n", "\t "])
    def test_blank_in_any_form(self, question):
        with pytest.raises(EntryError, match="needs a question"):
            Entry(question=question, answer="An answer.")

    def test_the_message_shows_the_answer_so_the_row_can_be_found(self):
        with pytest.raises(EntryError, match="Use the Forgot password"):
            Entry(question="", answer="Use the Forgot password link.")
