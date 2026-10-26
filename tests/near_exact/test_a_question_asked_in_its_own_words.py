"""A query that sits entirely inside an entry's phrasing.

Which is what a visitor does when the question is on the page in front of
them, or when the owner wrote the entry from a question they were actually
asked. The weighted comparison cannot see it when the shared words are
stopwords: "what are you working on" shares five of the seven tokens in
"What are you working on right now?" and all but one are stopwords, so by
content alone it matched a single word that another entry held too — and a
question that was practically quoted scored 0.489 and was refused.
"""

from __future__ import annotations

import pytest

from lexmatch import Index
from tests.near_exact.entries import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestAQuestionAskedInItsOwnWords:
    def test_it_is_answered(self, index):
        reply = index.reply("what are you working on")
        assert reply.answered, f"refused at {reply.score:.3f}"
        assert reply.entry.answer == "WORKING"

    def test_it_beats_an_entry_sharing_only_the_content_word(self, index):
        """ "work" is in four of these five entries."""
        ranked = index.score("what are you working on")
        assert ranked[0][1].answer == "WORKING"
        assert ranked[0][0] > ranked[1][0]

    def test_the_score_is_the_coverage(self, index):
        """Five query tokens inside seven: 2*5/(5+7)."""
        assert abs(index.score("what are you working on")[0][0] - 0.833) < 0.001

    def test_a_query_matching_the_phrasing_exactly_is_still_one(self, index):
        assert index.score("are you open to remote work")[0][0] == 1.0
