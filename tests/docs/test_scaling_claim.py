"""TestScalingClaim."""

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


class TestScalingClaim:
    def test_scores_are_bounded_zero_to_one(self, index):
        """README: 'Scores are scaled to 0-1, so a threshold means the same
        thing whatever the corpus size'."""
        for score, _ in index.score("remote work and relocation"):
            assert 0.0 <= score <= 1.0

    def test_the_threshold_means_the_same_at_a_different_corpus_size(self):
        entries = [
            Entry(f"Question number {number}?", f"Answer {number}", aliases=[f"q{number}"])
            for number in range(50)
        ]
        large = Index(entries)
        entry, score = large.answer("Question number 7?")
        assert entry is not None
        assert score == pytest.approx(1.0)
