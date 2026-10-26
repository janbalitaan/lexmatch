"""The worst of the old behaviour: two entries tied and one was picked."""

from __future__ import annotations

import pytest

from lexmatch import Index, Outcome, Tuning
from lexmatch.exceptions import TuningError
from tests.chat.a_chatbot_turn import ENTRIES, FIRST, FOURTH, SECOND, THIRD


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestAnAmbiguousQuestion:
    """The worst of the old behaviour: two entries tied and one was picked."""

    def test_the_old_behaviour_picked_one_silently(self, index):
        """`answer()` still does, which is why `reply()` exists."""
        ranked = index.score("what is your rate")
        assert abs(ranked[0][0] - ranked[1][0]) < 0.001, "the tie is the premise"
        assert index.answer("what is your rate")[0] is not None

    def test_reply_says_it_is_ambiguous(self, index):
        reply = index.reply("what is your rate")
        assert reply.outcome is Outcome.AMBIGUOUS
        assert not reply.answered

    def test_it_offers_both(self, index):
        reply = index.reply("what is your rate")
        assert len(reply.alternatives) == 2
        questions = {entry.question for entry in reply.alternatives}
        assert questions == {
            "What is your rate for design work?",
            "What is your rate for review work?",
        }

    def test_there_is_no_text_to_say(self, index):
        """So a caller writing `reply.text or ask_which()` behaves."""
        assert index.reply("what is your rate").text == ""

    def test_the_suggestions_are_the_alternatives(self, index):
        reply = index.reply("what is your rate")
        assert set(reply.suggestions) == {entry.question for entry in reply.alternatives}

    def test_a_wider_margin_finds_more_ambiguity(self):
        """Tested on `_contenders` rather than through a corpus.

        The margin decides how far below the best score an entry may sit and
        still count as a contender, which is arithmetic. Driving it through
        an index needs a corpus whose scores form a graded tail, and the
        scorer no longer produces one — weighting the overlap by inverse
        document frequency puts a non-matching entry at exactly 0.000, so
        every fixture that used to grade now has two scores and a cliff.
        Testing the arithmetic through that corpus tested the corpus.
        """
        ranked = [(0.90, FIRST), (0.88, SECOND), (0.70, THIRD), (0.40, FOURTH)]
        narrow = Index([FIRST], tuning=Tuning(ambiguity_margin=0.01))
        wide = Index([FIRST], tuning=Tuning(ambiguity_margin=0.25))
        assert len(narrow._contenders(ranked, 0.90)) == 1
        assert len(wide._contenders(ranked, 0.90)) == 3

    def test_a_non_matching_entry_is_never_a_contender(self):
        """However wide the margin. The threshold comes first."""
        ranked = [(0.90, FIRST), (0.00, SECOND)]
        wide = Index([FIRST], tuning=Tuning(ambiguity_margin=1.0))
        assert len(wide._contenders(ranked, 0.90)) == 1

    def test_a_zero_margin_only_catches_an_exact_tie(self):
        exact = Index(ENTRIES, tuning=Tuning(ambiguity_margin=0.0))
        assert exact.reply("what is your rate").outcome is Outcome.AMBIGUOUS

    def test_a_negative_margin_is_refused(self):
        with pytest.raises(TuningError, match="cannot be negative"):
            Tuning(ambiguity_margin=-0.1)
