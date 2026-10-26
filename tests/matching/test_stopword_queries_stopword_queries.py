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
