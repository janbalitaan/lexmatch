"""A query of pure filler is inside a great many questions.

"what do you do" covers three of the four tokens in dozens of phrasings, so
containment made it a near-exact match for all of them at once and the tie
was refused. Coverage alone does not catch that, because the coverage is
genuinely high — so containment is only tried when the query has a
substantive word in it.
"""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index
from tests.near_exact.entries import ENTRIES


class TestFillerIsNotNearExact:
    def test_a_filler_query_is_not_lifted_against_every_entry(self):
        index = Index(ENTRIES)
        ranked = index.score("what do you")
        lifted = [score for score, _ in ranked if score >= 0.70]
        assert len(lifted) < 2, f"{len(lifted)} entries lifted by filler"

    def test_a_filler_query_that_is_an_entry_still_matches_exactly(self):
        """Nothing is lost: the exact-match check covers it."""
        index = Index([*ENTRIES, Entry("What do you do?", "JOB", ["your job"])])
        assert index.reply("what do you do").entry.answer == "JOB"

    def test_the_small_talk_path_still_works(self):
        """The other reason a filler query is allowed to match on filler."""
        index = Index([*ENTRIES, Entry("How are you?", "FINE", ["how is it going"])])
        assert index.reply("how are you").entry.answer == "FINE"

    @pytest.mark.parametrize("query", ["what do you", "do you", "what is it"])
    def test_filler_does_not_answer_a_content_entry(self, query):
        index = Index(ENTRIES)
        reply = index.reply(query)
        assert not reply.answered or reply.score < 0.9
