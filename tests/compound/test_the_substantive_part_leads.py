"""A greeting in front of a question must not become the answer.

"Hi — do you have capacity for three months?" answers the greeting and
the question both. Headlining the greeting reads as having ignored the
question, and two such messages were answered with "Hello." at 1.000
while the real answer sat in `alternatives`."""

from __future__ import annotations

from typing import ClassVar

import pytest

from lexmatch import Entry, Index, SmallTalk
from tests.compound.a_message_asking_several_things import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestTheSubstantivePartLeads:
    """A greeting in front of a question must not become the answer.

    "Hi — do you have capacity for three months?" answers the greeting and
    the question both. Headlining the greeting reads as having ignored the
    question, and two such messages were answered with "Hello." at 1.000
    while the real answer sat in `alternatives`.
    """

    GREETED: ClassVar[list[Entry]] = [
        *SmallTalk.entries(
            {
                "greeting": "Hello.",
                "farewell": "Bye.",
                "thanks": "Ta.",
                "identity": "A bot.",
                "capability": "Ask away.",
                "wellbeing": "Fine.",
            }
        ),
        Entry(
            question="What is your notice period?",
            answer="NOTICE",
            aliases=["notice", "capacity", "availability"],
        ),
        Entry(question="What are your rates?", answer="RATE", aliases=["rate", "day rate"]),
    ]

    def test_the_question_is_the_answer(self):
        reply = Index(self.GREETED).reply("hi there! what is your notice period?")
        assert reply.entry.answer == "NOTICE"

    def test_the_greeting_is_carried_alongside(self):
        reply = Index(self.GREETED).reply("hi there! what is your notice period?")
        assert "Hello." in [entry.answer for entry in reply.alternatives]

    def test_a_greeting_alone_is_still_the_answer(self):
        assert Index(self.GREETED).reply("hi there").entry.answer == "Hello."

    def test_the_stronger_substantive_answer_leads(self):
        """Within the substantive group, by score."""
        reply = Index(self.GREETED).reply("hello. notice period? rates?")
        assert reply.entry.answer in {"NOTICE", "RATE"}
        assert "Hello." in [entry.answer for entry in reply.alternatives]
