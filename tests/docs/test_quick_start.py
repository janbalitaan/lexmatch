"""TestQuickStart."""

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


class TestQuickStart:
    def test_the_documented_match_and_score(self, index):
        """README: answer('what is your role') -> (Entry('What do you do?'), 1.0)."""
        entry, score = index.answer("what is your role")
        assert entry is not None
        assert entry.question == "What do you do?"
        assert score == pytest.approx(1.0)

    def test_the_documented_refusal(self, index):
        """README: answer('what is the capital of France') -> (None, 0.0)."""
        assert index.answer("what is the capital of France") == (None, 0.0)
