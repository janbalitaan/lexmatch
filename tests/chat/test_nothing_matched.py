"""Nothing matched."""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index, Outcome
from tests.chat.a_chatbot_turn import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestNothingMatched:
    def test_it_is_unanswered(self, index):
        reply = index.reply("what is the weather")
        assert reply.outcome is Outcome.UNANSWERED
        assert not reply.answered

    def test_suggestions_are_offered(self, index):
        assert index.reply("what is the weather").suggestions

    def test_near_misses_are_ranked_by_relevance(self):
        """A query that nearly matched gets what it nearly matched, not the
        first entries in the list.

        `"work"` scores partially against the two entries containing it and
        zero against the rest, so those two are what it should be offered —
        in score order, and nothing else.
        """
        index = Index(ENTRIES, threshold=0.99)
        reply = index.reply("work")
        assert reply.outcome is Outcome.UNANSWERED
        assert 0 < reply.score < 0.99, f"not a near miss: {reply.score:.3f}"
        assert len(reply.suggestions) == 3
        assert "remote work" in reply.suggestions[0].lower()

    def test_a_near_miss_offers_only_what_scored(self):
        """An entry scoring zero is not a near miss and is not offered.

        A dedicated index, because finding a query that partially matches
        exactly one entry depends on the whole corpus through IDF — in the
        shared fixture "notice" reaches 0.996 and is simply answered.
        """
        index = Index(
            [
                Entry(question="Which design tools do you use?", answer="Figma."),
                Entry(question="Are you open to remote work?", answer="Yes."),
            ],
            threshold=0.99,
        )
        reply = index.reply("tools")
        assert reply.outcome is Outcome.UNANSWERED
        assert 0 < reply.score < 0.99, f"not a near miss: {reply.score:.3f}"
        assert reply.suggestions == ("Which design tools do you use?",)

    def test_a_query_with_no_overlap_falls_back_to_the_list(self, index):
        """There is no near miss to offer, and the first few questions are at
        least an honest menu."""
        reply = index.reply("xyzzy plugh")
        assert reply.suggestions == tuple(index.suggestions(limit=3))

    def test_an_empty_index_says_unanswered(self):
        assert Index([]).reply("anything").outcome is Outcome.UNANSWERED

    def test_an_empty_query_says_unanswered(self, index):
        assert index.reply("").outcome is Outcome.UNANSWERED
