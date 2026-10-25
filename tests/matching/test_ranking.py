"""TestRanking."""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index


@pytest.fixture
def entries() -> list[Entry]:
    return [
        Entry(
            "What do you do?",
            "I build backend services.",
            aliases=["what is your job", "what is your role"],
            tags=["opening"],
        ),
        Entry(
            "Are you open to remote work?",
            "Yes, and to relocation.",
            aliases=["remote", "relocate", "would you move"],
            tags=["logistics"],
        ),
        Entry(
            "Tell me about a time you made a mistake",
            "I shipped a migration with no rollback.",
            aliases=["a failure", "something you got wrong"],
            tags=["experience"],
        ),
        Entry(
            "What are your salary expectations?",
            "Let us discuss that in context.",
            aliases=["salary", "compensation", "rate"],
            tags=["boundary"],
        ),
    ]


@pytest.fixture
def index(entries) -> Index:
    return Index(entries)


class TestRanking:
    def test_the_distinctive_word_decides(self, index):
        """The distinctive word must outrank shared filler.

        'tell me about' appears in several entries, so if those words carry
        weight the query lands on whichever entry shares the most filler
        rather than the one sharing the meaningful word.
        """
        entry, _ = index.answer("tell me about a failure")
        assert entry is not None
        assert "mistake" in entry.question.lower()

    def test_scores_are_bounded(self, index):
        for score, _ in index.score("tell me about remote work and salary"):
            assert 0.0 <= score <= 1.0

    def test_results_are_ordered_best_first(self, index):
        scores = [score for score, _ in index.score("salary expectations")]
        assert scores == sorted(scores, reverse=True)
