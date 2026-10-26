"""Several answers."""

from __future__ import annotations

import pytest

from lexmatch import Index
from tests.chat.composing_a_reply import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestSeveralAnswers:
    def test_each_answer_appears(self, index):
        said = index.respond("remote? and notice period?")
        assert "remotely for six years" in said
        assert "one month's notice" in said

    def test_the_last_takes_a_connective(self, index):
        """Three statements adjacent read as a dump; a connective makes them
        a list."""
        assert "And " in index.respond("remote? and notice period?")

    def test_the_word_after_the_connective_is_lower_cased(self, index):
        """ "And Yes, I have" reads wrong."""
        said = index.respond("notice period? and remote?")
        assert "And yes" in said
        assert "And Yes" not in said

    def test_the_order_asked_is_the_order_answered(self, index):
        said = index.respond("notice period? and design rate?")
        assert said.index("one month") < said.index("£600")
