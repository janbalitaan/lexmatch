"""A missing answer is refused."""

from __future__ import annotations

import pytest

from lexmatch import Entry, EntryError


class TestAMissingAnswerIsRefused:
    @pytest.mark.parametrize("answer", ["", "   ", "\n"])
    def test_blank_in_any_form(self, answer):
        with pytest.raises(EntryError, match="needs an answer"):
            Entry(question="What do you do?", answer=answer)

    def test_the_message_shows_the_question(self):
        with pytest.raises(EntryError, match="What do you do"):
            Entry(question="What do you do?", answer="")
