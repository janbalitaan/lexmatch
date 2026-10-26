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

from typing import ClassVar

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


FIRST = Entry(question="What is your rate for design work?", answer="£600.")
SECOND = Entry(question="What is your rate for review work?", answer="£500.")
THIRD = Entry(question="What is your rate for audit work?", answer="£550.")
FOURTH = Entry(question="What is your notice period?", answer="One month.")


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


class TestAWeakTieIsNotAmbiguity:
    """A tie among weak matches is a question that was not understood.

    This guard was added when "what do you work on" tied four ways at 0.537
    and asked "remote work, or visa sponsorship?" — which read as nonsense.
    That tie no longer happens: it was an artifact of weighting every shared
    token equally, and once phrase overlap was weighted by inverse document
    frequency the same query scored 0.637 against one entry and 0.133 against
    the rest. The first test below pins that, because it is the real fix and
    a regression in it would be invisible otherwise.

    The floor stays as a guard and a knob. These tests widen the margin to
    force a tie, because a natural one no longer occurs in a fixture this
    size — which is the point.
    """

    COMMON: ClassVar[list[Entry]] = [
        Entry(question="Are you open to remote work?", answer="Yes.", aliases=["remote"]),
        Entry(
            question="Can you start work next month?", answer="Soon.", aliases=["availability"]
        ),
        Entry(question="Do you enjoy the work?", answer="Very much.", aliases=["enjoyment"]),
        Entry(question="Is the work interesting?", answer="Usually.", aliases=["interest"]),
    ]
    #: A shared "work" plus filler, well under the threshold.
    WEAK = "you work"
    #: A realistic index. Two entries that differ by one word score poorly
    #: against everything, because every word they share has a low inverse
    #: document frequency — so a fixture of only those tests the dilution
    #: rather than the behaviour under test.
    RATES: ClassVar[list[Entry]] = [
        Entry(question="What is your rate for design work?", answer="DESIGN"),
        Entry(question="What is your rate for review work?", answer="REVIEW"),
        Entry(question="What is your notice period?", answer="NOTICE", aliases=["notice"]),
        Entry(question="Are you open to remote work?", answer="REMOTE", aliases=["remote"]),
        Entry(question="Do you need visa sponsorship?", answer="VISA", aliases=["visa"]),
        Entry(question="What is your tech stack?", answer="STACK", aliases=["stack"]),
        Entry(question="Have you led a team?", answer="LEAD", aliases=["leadership"]),
        Entry(question="How many years of experience?", answer="YEARS", aliases=["experience"]),
    ]

    def test_filler_scores_near_nothing(self):
        """The regression guard for the weighting that made the floor moot.

        "what do you work on" once tied four ways at 0.537 and produced a
        clarifying question listing unrelated entries. Weighting the overlap
        by inverse document frequency, and then confining the comparison to
        content words, left it scoring almost nothing at all — which is the
        honest reading of a question whose only substantive word is in every
        entry.
        """
        ranked = Index(self.COMMON).score("what do you work on")
        assert ranked[0][0] < Index(self.COMMON).threshold, (
            f"filler scored {ranked[0][0]:.3f}, over the threshold"
        )

    def test_a_weak_tie_is_reported_as_unanswered(self):
        forced = Index(self.COMMON, tuning=Tuning(ambiguity_margin=0.2))
        assert forced.reply(self.WEAK).outcome is Outcome.UNANSWERED

    def test_the_contenders_are_offered_as_suggestions(self):
        """So the asker chooses rather than the index guessing."""
        forced = Index(self.COMMON, tuning=Tuning(ambiguity_margin=0.2, threshold=0.1))
        assert forced.reply(self.WEAK).suggestions

    def test_lowering_the_floor_makes_it_ambiguity_again(self):
        loose = Index(
            self.COMMON,
            tuning=Tuning(ambiguity_margin=0.2, ambiguity_floor=0.0, threshold=0.1),
        )
        assert loose.reply(self.WEAK).outcome is Outcome.AMBIGUOUS

    def test_a_confident_tie_is_still_ambiguity(self):
        """Two rate entries among six others, and a query naming neither:
        0.744, over the floor, and asking which was meant is right."""
        index = Index(self.RATES)
        reply = index.reply("what is your rate")
        assert reply.outcome is Outcome.AMBIGUOUS
        assert reply.score >= index.tuning.ambiguity_floor
        assert {entry.answer for entry in reply.alternatives} == {"DESIGN", "REVIEW"}

    def test_at_most_three_alternatives_are_offered(self):
        """Two is a question; five is a menu, and a menu is what
        `suggestions` is for."""
        many = [
            Entry(question=f"What is your rate for {kind} work?", answer="A.")
            for kind in ("design", "review", "audit", "training", "advisory")
        ]
        reply = Index(many, tuning=Tuning(ambiguity_margin=0.9)).reply("what is your rate")
        assert len(reply.alternatives) <= 3

    def test_a_floor_outside_zero_to_one_is_refused(self):
        with pytest.raises(TuningError, match="between 0 and 1"):
            Tuning(ambiguity_floor=1.5)
