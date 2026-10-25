"""TestMatching."""

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


class TestMatching:
    def test_an_exact_question_scores_top(self, index):
        entry, score = index.answer("What do you do?")
        assert entry is not None
        assert entry.question == "What do you do?"
        assert score == pytest.approx(1.0)

    @pytest.mark.parametrize("phrasing", ["what is your job", "what is your role"])
    def test_aliases_match(self, index, phrasing):
        entry, _ = index.answer(phrasing)
        assert entry is not None
        assert entry.question == "What do you do?"

    def test_a_single_distinctive_word_matches(self, index):
        entry, _ = index.answer("salary")
        assert entry is not None
        assert "salary" in entry.question.lower()

    def test_an_unlisted_phrasing_does_not_match(self):
        """Without a model there is no way to know 'role' means 'job'.

        Documented rather than worked around: listing the phrasing is the fix,
        and pretending otherwise would make the threshold meaningless.
        """
        index = Index([Entry("What do you do?", "Backend.", aliases=["what is your job"])])
        assert index.answer("what is your role")[0] is None
