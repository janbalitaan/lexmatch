"""The loose split is a second opinion, discarded unless it finds more.

"are you open to remote and hybrid work" splits loosely into two halves
that answer the same entry — so the loose reading finds the same single
answer, gains nothing, and the strict reading is kept. Keeping the loose
one would report "hybrid work" as unanswered on a question that *was*
answered."""

from __future__ import annotations

from typing import ClassVar

import pytest

from lexmatch import Entry, Index, QuestionSplitter
from tests.compound.a_message_asking_several_things import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestTheStrictReadingSurvivesWhenLooseGainsNothing:
    """The loose split is a second opinion, discarded unless it finds more.

    "are you open to remote and hybrid work" splits loosely into two halves
    that answer the same entry — so the loose reading finds the same single
    answer, gains nothing, and the strict reading is kept. Keeping the loose
    one would report "hybrid work" as unanswered on a question that *was*
    answered.
    """

    SHARED: ClassVar[list[Entry]] = [
        Entry(question="Are you open to remote and hybrid work?", answer="Both.", aliases=[]),
        Entry(
            question="What is your notice period?",
            answer="One month.",
            aliases=["availability"],
        ),
    ]

    def test_the_whole_question_is_answered(self):
        index = Index(self.SHARED)
        found = index.answers("are you open to remote and hybrid work?")
        assert len(found) == 1
        assert found[0][0].answer == "Both."

    def test_nothing_is_reported_as_missed(self):
        index = Index(self.SHARED)
        assert index.unanswered("are you open to remote and hybrid work?") == []

    def test_the_loose_split_really_would_have_split_it(self):
        """So the test is exercising the discard rather than a split that
        never happened."""
        assert (
            len(QuestionSplitter.split_loosely("are you open to remote and hybrid work?")) == 2
        )
        assert len(QuestionSplitter.split("are you open to remote and hybrid work?")) == 1

    def test_and_the_loose_one_wins_when_it_does_find_more(self):
        """ "remote and notice period" has no interrogative after the "and",
        so the strict rule keeps it whole and answers one of the two. The
        loose rule answers both, which is the evidence that they were
        separate questions."""
        index = Index(self.SHARED)
        strict = QuestionSplitter.split("remote and notice period")
        loose = QuestionSplitter.split_loosely("remote and notice period")
        assert len(strict) == 1, "the premise: the strict rule keeps it whole"
        assert len(loose) == 2
        assert len(index.answers("remote and notice period")) == 2
