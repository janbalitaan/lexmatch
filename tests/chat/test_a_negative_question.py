"""Lexical matching cannot tell a question from its negation: they share
every substantive word, and the negating words are stopwords."""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index, Outcome
from tests.chat.a_chatbot_turn import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestANegativeQuestion:
    """Lexical matching cannot tell a question from its negation: they share
    every substantive word, and the negating words are stopwords."""

    def test_the_old_behaviour_answered_the_opposite(self, index):
        """0.923 against the affirmative entry, answered "Yes"."""
        entry, score = index.answer("are you not open to remote work")
        assert entry is not None
        assert entry.answer == "Yes."
        assert score > 0.9

    def test_reply_marks_it(self, index):
        reply = index.reply("are you not open to remote work")
        assert reply.outcome is Outcome.NEGATED
        assert not reply.answered

    def test_there_is_no_text_to_say(self, index):
        assert index.reply("are you not open to remote work").text == ""

    def test_the_closest_match_is_still_reported(self, index):
        """So a caller can answer carefully rather than not at all."""
        reply = index.reply("are you not open to remote work")
        assert reply.alternatives[0].question == "Are you open to remote work?"

    def test_an_affirmative_question_is_unaffected(self, index):
        assert index.reply("are you open to remote work").outcome is Outcome.ANSWERED

    def test_two_negatives_agree(self):
        """Both negative is not a mismatch; it is the mismatch that inverts."""
        entries = [Entry(question="Are you not available?", answer="I am.")]
        assert Index(entries).reply("aren't you available").outcome is Outcome.ANSWERED
