"""TestAliasesClaim."""

from __future__ import annotations

import pytest

from lexmatch import (
    Entry,
    Index,
)


@pytest.fixture
def index() -> Index:
    """The exact index the README's opening example builds."""
    return Index(
        [
            Entry(
                "What do you do?",
                "I build backend services.",
                aliases=["what is your job", "what is your role"],
            ),
            Entry(
                "Are you open to remote work?",
                "Yes, and to relocation.",
                aliases=["remote", "relocate", "would you move", "hybrid"],
            ),
        ]
    )


class TestAliasesClaim:
    def test_aliases_are_weighted_as_heavily_as_the_question(self, index):
        """README: 'Aliases are weighted as heavily as the question itself'."""
        by_question = index.answer("What do you do?")[1]
        by_alias = index.answer("what is your job")[1]
        assert by_alias == pytest.approx(by_question)

    def test_a_single_alias_word_matches(self, index):
        entry, _ = index.answer("remote")
        assert entry is not None
        assert "remote" in entry.question.lower()
