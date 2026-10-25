"""TestRefusal."""

from __future__ import annotations

import pytest

from lexmatch import DEFAULT_THRESHOLD, Entry, Index


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


class TestRefusal:
    @pytest.mark.parametrize(
        "query",
        ["what is the capital of France", "write me a poem", "what is 2+2", "zzzz"],
    )
    def test_off_topic_questions_are_refused(self, index, query):
        entry, score = index.answer(query)
        assert entry is None, f"{query!r} matched at {score:.2f}"

    def test_shared_filler_alone_never_matches(self, index):
        """Overlapping filler is not a match.

        'what is 2+2' shares 'what is' with 'what is your job'. Phrase
        scoring therefore requires the substantive words to overlap too,
        or every question beginning 'what is' would match.
        """
        assert index.answer("what is 2+2")[0] is None

    def test_the_default_threshold_sits_above_filler_noise(self):
        assert DEFAULT_THRESHOLD > 0.4

    def test_a_threshold_of_one_refuses_everything(self, entries):
        assert Index(entries, threshold=1.01).answer("What do you do?")[0] is None

    def test_a_threshold_of_zero_accepts_anything(self, entries):
        assert Index(entries, threshold=0.0).answer("zzz unrelated")[0] is not None
