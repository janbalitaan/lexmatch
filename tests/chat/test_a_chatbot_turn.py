"""The three ways a query fails, each needing a different thing said.

`answer()` returns a pair, which is enough to know whether anything matched.
It is not enough to behave like a chatbot:

    nothing matched       "I don't know that. Try one of these."
    two matched equally   "Which did you mean — design or review?"
    a negative question   the closest match is the opposite of the answer

Collapsing those into `(None, 0.0)` is how a bot comes to answer about
design rates when it was asked about rates. Worse, the ambiguous case did
not even return None — it picked the first of two entries tied at 0.727,
which is a confident wrong answer half the time with no way for the visitor
to tell which half they got.
"""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index, Outcome, Reply, Tuning
from lexmatch.exceptions import TuningError

ENTRIES = [
    Entry(
        question="What is your rate for design work?",
        answer="£600/day for design.",
        aliases=["design rate"],
    ),
    Entry(
        question="What is your rate for review work?",
        answer="£500/day for review.",
        aliases=["review rate"],
    ),
    Entry(question="Are you open to remote work?", answer="Yes.", aliases=["remote"]),
    Entry(
        question="What is your notice period?", answer="One month.", aliases=["availability"]
    ),
]


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestAClearMatch:
    def test_it_is_answered(self, index):
        reply = index.reply("design rate")
        assert reply.outcome is Outcome.ANSWERED
        assert reply.answered

    def test_the_text_is_the_answer(self, index):
        assert index.reply("design rate").text == "£600/day for design."

    def test_there_are_no_alternatives(self, index):
        assert index.reply("design rate").alternatives == ()

    def test_the_score_is_carried(self, index):
        assert index.reply("design rate").score > 0.9


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
        """Only entries that *cleared the threshold* can be contenders — an
        entry scoring zero is not a candidate however wide the margin. So
        the margin is tested where three entries genuinely compete."""
        competing = [
            Entry(question="What is your rate for design work?", answer="£600."),
            Entry(question="What is your rate for review work?", answer="£500."),
            Entry(question="What is your rate for audit work?", answer="£550."),
        ]
        narrow = Index(competing, tuning=Tuning(ambiguity_margin=0.0))
        wide = Index(competing, tuning=Tuning(ambiguity_margin=0.9))
        query = "what is your rate for consulting work"
        assert len(wide.reply(query).alternatives) >= len(narrow.reply(query).alternatives)
        assert len(wide.reply(query).alternatives) == 3

    def test_a_zero_margin_only_catches_an_exact_tie(self):
        exact = Index(ENTRIES, tuning=Tuning(ambiguity_margin=0.0))
        assert exact.reply("what is your rate").outcome is Outcome.AMBIGUOUS

    def test_a_negative_margin_is_refused(self):
        with pytest.raises(TuningError, match="cannot be negative"):
            Tuning(ambiguity_margin=-0.1)


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


class TestTheReplyItself:
    def test_describe_carries_the_shape(self, index):
        described = index.reply("what is your rate").describe()
        assert "ambiguous" in described
        assert "2 alternatives" in described

    def test_describe_holds_no_question_or_answer_text(self, index):
        """A log of what visitors asked is personal data, and its retention
        should be deliberate rather than a side effect of debugging."""
        described = index.reply("design rate").describe()
        assert "design rate" not in described
        assert "£600" not in described

    def test_a_bare_reply_is_unanswered(self):
        assert not Reply(outcome=Outcome.UNANSWERED).answered

    def test_the_outcome_serializes_as_its_name(self):
        """It ends up in JSON more often than not."""
        assert Outcome.AMBIGUOUS == "ambiguous"
        assert f"{Outcome.ANSWERED.value}" == "answered"
