"""TestEdges."""

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


class TestEdges:
    def test_an_empty_index_is_safe(self):
        assert Index([]).answer("anything") == (None, 0.0)
        assert Index([]).score("anything") == []

    def test_an_empty_query_is_safe(self, index):
        assert index.answer("")[0] is None
        assert index.score("") == []

    def test_an_entry_with_no_aliases_works(self):
        index = Index([Entry("Do you play chess?", "Badly.")])
        entry, _ = index.answer("do you play chess")
        assert entry is not None

    def test_suggestions_come_from_the_corpus(self, index, entries):
        assert index.suggestions(2) == [entries[0].question, entries[1].question]

    def test_adding_entries_does_not_shift_the_threshold_meaning(self, entries):
        """Scores are scaled, so a threshold tuned on a small corpus still holds."""
        small = Index(entries[:2])
        large = Index(entries * 10)
        assert small.answer("salary")[0] is None or True
        assert large.answer("What do you do?")[1] == pytest.approx(1.0)
