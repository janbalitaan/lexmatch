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
size — which is the point."""

from __future__ import annotations

from typing import ClassVar

import pytest

from lexmatch import Entry, Index, Outcome, Tuning
from lexmatch.exceptions import TuningError
from tests.chat.a_chatbot_turn import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


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
