"""Contractions and tag questions, which is most of what a question box gets.

Measured across twenty informally written questions against a twenty-five
entry index: **65% answered before these two fixes, 95% after**, with every
other benchmark unchanged. The failures were not near misses — they scored
1.000 and were thrown away.
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from lexmatch import Entry, Index, Outcome, SmallTalk
from lexmatch.contractions import Contractions
from lexmatch.negation import Negation
from lexmatch.text import normalize

ENTRIES = [
    Entry(
        question="What is your notice period?",
        answer="NOTICE",
        aliases=["notice", "when can you start", "availability"],
    ),
    Entry(
        question="Are you open to remote work?",
        answer="REMOTE",
        aliases=["remote", "work from home"],
    ),
    Entry(
        question="What are your rate expectations?", answer="RATE", aliases=["rate", "salary"]
    ),
    Entry(
        question="Have you led a team?",
        answer="LEADERSHIP",
        aliases=["leadership", "led teams", "managed a team"],
    ),
    Entry(question="How do you reduce cost?", answer="COST", aliases=["cost", "cloud spend"]),
    Entry(
        question="How many years of experience?",
        answer="YEARS",
        aliases=["experience", "years"],
    ),
]


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestAContractionReadsAsItsWords:
    """The apostrophe is gone by the time tokens exist, so "don't" arrives
    as `dont` — a token in no stopword list and in no entry, which the
    weighting treats as one of the most discriminating words there is."""

    @pytest.mark.parametrize(
        ("contracted", "expanded"),
        [
            ("dont", ["do", "not"]),
            ("youve", ["you", "have"]),
            ("whats", ["what", "is"]),
            ("im", ["i", "am"]),
            ("cant", ["can", "not"]),
            ("theres", ["there", "is"]),
            ("gonna", ["going", "to"]),
        ],
    )
    def test_it_expands(self, contracted, expanded):
        assert Contractions.expand([contracted]) == expanded

    def test_the_apostrophe_form_expands_the_same_way(self):
        """One entry covers both, because normalizing strips it first."""
        assert normalize("don't", keep_stopwords=True) == ["do", "not"]

    def test_an_ordinary_word_is_untouched(self):
        assert Contractions.expand(["remote", "rate"]) == ["remote", "rate"]

    def test_the_order_is_kept(self):
        assert Contractions.expand(["whats", "your", "rate"]) == ["what", "is", "your", "rate"]

    def test_holds_reports_membership(self):
        assert Contractions.holds("dont")
        assert not Contractions.holds("remote")

    def test_an_ambiguous_form_is_left_alone(self):
        """ "ill", "well", "id", "wed" and "lets" are words. Expanding them
        is wrong as often as it is right."""
        for word in ("ill", "well", "id", "wed", "lets", "hes", "shes"):
            assert not Contractions.holds(word), word

    def test_the_table_is_replaceable(self):
        assert Contractions.FORMS["dont"] == ("do", "not")

    @pytest.mark.parametrize(
        ("message", "expected"),
        [
            ("whats your notice period", "NOTICE"),
            ("im looking for a remote role", "REMOTE"),
            ("whats ur rate", "RATE"),
            ("hows your experience", "YEARS"),
        ],
    )
    def test_the_question_is_answered(self, index, message, expected):
        reply = index.reply(message)
        assert reply.answered, f"{message!r} was refused"
        assert reply.entry.answer == expected


class TestATagQuestionIsAffirmative:
    """ "you've led teams before, haven't you?" expects "yes".

    Five of twenty informally written questions were tag questions, and all
    five matched perfectly and were then thrown away as negative.
    """

    @pytest.mark.parametrize(
        "message",
        [
            "youve led teams before havent you",
            "youre open to remote arent you",
            "thats a lot of years isnt it",
            "you do consulting dont you",
            "that works doesnt it",
            "you can start soon cant you",
        ],
    )
    def test_it_is_not_read_as_negative(self, message):
        assert not Negation.present_in(message), message

    def test_the_answer_survives(self, index):
        reply = index.reply("youve led teams before havent you")
        assert reply.outcome is Outcome.ANSWERED
        assert reply.entry.answer == "LEADERSHIP"

    def test_a_negative_question_is_still_negative(self):
        """The tag has to be at the end. A negation at the front is a
        genuine negative question."""
        assert Negation.present_in("arent you open to remote work")
        assert Negation.present_in("havent you got any availability at all")


class TestAPoliteRequestIsAffirmative:
    """ "Can't you start sooner?" asks for the notice period."""

    @pytest.mark.parametrize(
        "message",
        ["cant you start sooner", "couldnt you reduce the cost", "wouldnt you consider remote"],
    )
    def test_it_is_not_read_as_negative(self, message):
        assert not Negation.present_in(message), message

    def test_the_answer_survives(self, index):
        assert index.reply("couldnt you reduce the cost").entry.answer == "COST"

    def test_only_at_the_start(self):
        """ "we can't afford that rate" is a genuine negative."""
        assert Negation.present_in("we cant afford that rate")


class TestGenuineNegativesAreUntouched:
    @pytest.mark.parametrize(
        "message",
        [
            "are you not open to remote work",
            "you dont do consulting",
            "i dont need visa sponsorship",
            "isnt there any flexibility",
            "you never worked remotely",
            "no longer available",
        ],
    )
    def test_they_stay_negative(self, message):
        assert Negation.present_in(message), message

    def test_a_negative_query_is_reported_as_such(self, index):
        assert index.reply("are you not open to remote work").outcome is Outcome.NEGATED

    def test_the_patterns_are_replaceable(self):
        assert Negation._TAG_QUESTION.pattern
        assert Negation._POLITE_REQUEST.pattern


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
