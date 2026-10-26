"""Ambiguity is one question matching two entries.

Two questions matching one entry each is not that, and asking which was
meant answers neither. Measured: "yoe and tech stack?" tied at 0.586
between the experience and stack entries and asked which was meant,
while `answers()` on the same message had already resolved it to both —
`reply()` scored the whole string and never consulted the reading."""

from __future__ import annotations

from typing import ClassVar

import pytest

from lexmatch import Entry, Index, Outcome
from tests.compound.a_message_asking_several_things import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestAMessageThatAsksTwoThingsIsNotAmbiguous:
    """Ambiguity is one question matching two entries.

    Two questions matching one entry each is not that, and asking which was
    meant answers neither. Measured: "yoe and tech stack?" tied at 0.586
    between the experience and stack entries and asked which was meant,
    while `answers()` on the same message had already resolved it to both —
    `reply()` scored the whole string and never consulted the reading.
    """

    PAIR: ClassVar[list[Entry]] = [
        Entry(
            question="How many years of experience?",
            answer="YEARS",
            aliases=["yoe", "experience"],
        ),
        Entry(
            question="What is your tech stack?", answer="STACK", aliases=["tech stack", "stack"]
        ),
        Entry(question="What is your notice period?", answer="NOTICE", aliases=["notice"]),
        Entry(question="What are your rates?", answer="RATE", aliases=["rate"]),
    ]

    def test_it_is_answered_not_reported_ambiguous(self):
        reply = Index(self.PAIR).reply("yoe and tech stack?")
        assert reply.outcome is Outcome.ANSWERED

    def test_both_answers_are_carried(self):
        reply = Index(self.PAIR).reply("yoe and tech stack?")
        found = {reply.entry.answer, *(entry.answer for entry in reply.alternatives)}
        assert found == {"YEARS", "STACK"}

    def test_a_genuinely_ambiguous_question_is_still_ambiguous(self):
        """One question, two entries — which is what ambiguity means."""
        rates = [
            Entry(question="What is your rate for design work?", answer="DESIGN"),
            Entry(question="What is your rate for review work?", answer="REVIEW"),
            Entry(question="What is your notice period?", answer="NOTICE", aliases=["notice"]),
            Entry(question="Are you open to remote work?", answer="REMOTE", aliases=["remote"]),
            Entry(question="Do you need visa sponsorship?", answer="VISA", aliases=["visa"]),
            Entry(question="What is your tech stack?", answer="STACK", aliases=["stack"]),
        ]
        assert Index(rates).reply("what is your rate").outcome is Outcome.AMBIGUOUS
