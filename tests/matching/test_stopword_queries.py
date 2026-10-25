"""BM25 alone cannot rank these, which is why phrase scoring exists."""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index, query_terms


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


class TestStopwordQueries:
    """BM25 alone cannot rank these, which is why phrase scoring exists."""

    @pytest.mark.parametrize("query", ["what do you do", "what do you do?", "WHAT DO YOU DO"])
    def test_a_query_of_only_stopwords_still_matches(self, index, query):
        entry, _ = index.answer(query)
        assert entry is not None
        assert entry.question == "What do you do?"

    def test_query_terms_never_empty_for_real_input(self):
        assert query_terms("what do you do")
        assert query_terms("") == []


class TestPhraseScoringEdges:
    """Guards in the phrase scorer, reached directly.

    These two cannot be provoked through `answer()`: BM25 produces no
    candidate for a query that shares no term with any entry, so the scorer is
    never called for one. They are tested here because the guards are correct
    — the scorer should not assume its caller filtered the input — and a test
    is a better record of that than a coverage exemption.
    """

    def test_a_query_with_no_tokens_scores_zero(self, entries):
        """Normalizing "???" leaves nothing to compare."""
        index = Index(entries)
        assert index._phrase_score(0, "???") == 0.0

    def test_a_query_of_only_punctuation_is_refused(self, entries):
        """Through the public API it is refused before scoring."""
        answer, score = Index(entries).answer("???")
        assert answer is None
        assert score == 0.0

    def test_an_alias_that_normalizes_to_nothing_is_dropped(self):
        """It is dropped when the index is built, not skipped while scoring —
        which is why the scorer needs no guard for an empty phrase."""
        index = Index(
            [
                Entry(
                    "What do you do?",
                    "I build backend systems.",
                    aliases=["", "   ", "your work"],
                )
            ]
        )
        assert index.answer("What do you do?") is not None
        assert index.answer("your work") is not None
