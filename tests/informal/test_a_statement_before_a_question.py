"""A negative clause must not suppress the answer to the next one.

"I don't need visa sponsorship, what's the stack?" is a statement and a
question. Scoring the whole string reads the statement's "not" against
the question's answer and reports it negated — so a question that was
answered perfectly came back as nothing."""

from __future__ import annotations

from typing import ClassVar

import pytest

from lexmatch import Entry, Index, Outcome, SmallTalk
from tests.informal.how_people_actually_type import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestAStatementBeforeAQuestion:
    """A negative clause must not suppress the answer to the next one.

    "I don't need visa sponsorship, what's the stack?" is a statement and a
    question. Scoring the whole string reads the statement's "not" against
    the question's answer and reports it negated — so a question that was
    answered perfectly came back as nothing.
    """

    MIXED: ClassVar[list[Entry]] = [
        Entry(
            question="What is your tech stack?", answer="STACK", aliases=["stack", "tech stack"]
        ),
        Entry(
            question="Do you need visa sponsorship?",
            answer="VISA",
            aliases=["visa", "sponsorship"],
        ),
        Entry(question="What is your notice period?", answer="NOTICE", aliases=["notice"]),
    ]

    def test_the_question_is_answered(self):
        index = Index(self.MIXED)
        reply = index.reply("I don't need visa sponsorship, what's the stack?")
        assert reply.answered, f"refused at {reply.score:.3f} as {reply.outcome.value}"
        assert reply.entry.answer == "STACK"

    def test_the_whole_string_alone_would_have_refused(self):
        """The premise, so this keeps testing the rescue."""
        index = Index(self.MIXED)
        whole = index._reply_to_one("I don't need visa sponsorship, what's the stack?")
        assert not whole.answered
        assert whole.outcome is Outcome.NEGATED

    def test_a_pleasantry_is_not_a_rescue(self):
        """Answering a question it cannot answer with "Hello" is worse than
        refusing — it reads as not having noticed the question."""
        greeted = [
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
            Entry(question="What is your notice period?", answer="NOTICE", aliases=["notice"]),
        ]
        reply = Index(greeted).reply("Good afternoon. What quantum compiler do you use?")
        assert not reply.answered or reply.entry.answer != "Hello."

    def test_a_whole_string_reply_that_answers_is_not_overridden(self):
        """Measured: overriding it cost 4.9 points across fifteen simulated
        visitors, because a message that splits is usually one question."""
        index = Index(self.MIXED)
        reply = index.reply("do you need visa sponsorship and a work permit?")
        assert reply.answered
