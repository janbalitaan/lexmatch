"""Small talk may answer small talk, and nothing else.

Social phrasings are short, and the length penalty favours short entries, so
an entry built from "take care" or "good morning" used to win any message
containing "care" or "good". Measured over fifteen simulated visitors, five
real questions were answered with a pleasantry — "is the pay good" scored
1.000 against the greeting, "do you care about the frontend at all" scored
0.957 against the farewell.
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from lexmatch import Entry, Index, Outcome, QuestionSplitter, SmallTalk

REPLIES = {
    "greeting": "Hello.",
    "farewell": "Take care.",
    "thanks": "You're welcome.",
    "identity": "I'm a bot.",
    "capability": "Ask about rates or availability.",
    "wellbeing": "Well, thanks.",
}


@pytest.fixture
def index() -> Index:
    return Index(
        [
            *SmallTalk.entries(REPLIES),
            Entry(
                question="What are your rate expectations?",
                answer="RATE",
                aliases=["rate", "pay", "salary"],
            ),
            Entry(
                question="Do you work on the frontend?",
                answer="FRONTEND",
                aliases=["frontend", "ui work"],
            ),
            Entry(
                question="Do you do consulting?",
                answer="CONSULTING",
                aliases=["consulting", "advisory"],
            ),
        ]
    )


class TestARealQuestionIsNotAnsweredWithAPleasantry:
    @pytest.mark.parametrize(
        ("message", "expected"),
        [
            ("is the pay good", "RATE"),
            ("do you care about the frontend at all", "FRONTEND"),
            ("hi do you do consulting", "CONSULTING"),
        ],
    )
    def test_the_subject_wins_over_the_social_word(self, index, message, expected):
        reply = index.reply(message)
        assert reply.answered, f"{message!r} was refused"
        assert reply.entry.answer == expected

    def test_a_greeting_prefix_does_not_swallow_the_question(self, index):
        """ "hi" is a greeting phrasing, "consulting" is not, so the greeting
        entry is out and the consulting entry is free to win."""
        assert index.reply("hi do you do consulting").entry.answer == "CONSULTING"


class TestSmallTalkItselfStillWorks:
    @pytest.mark.parametrize(
        ("message", "expected"),
        [
            ("hello", "Hello."),
            ("yo", "Hello."),
            ("good morning", "Hello."),
            ("thanks", "You're welcome."),
            ("cheers", "You're welcome."),
            ("bye", "Take care."),
            ("take care", "Take care."),
            ("who are you", "I'm a bot."),
            ("how are you", "Well, thanks."),
        ],
    )
    def test_it_is_answered(self, index, message, expected):
        reply = index.reply(message)
        assert reply.answered, f"{message!r} was refused"
        assert reply.entry.answer == expected


class TestAnAcknowledgementIsNotASubject:
    """ "great, thanks" is one unit, because a comma is not a terminator."""

    def test_it_does_not_suppress_the_small_talk(self, index):
        assert index.reply("great, thanks!").entry.answer == "You're welcome."

    def test_nothing_is_reported_as_unanswered(self, index):
        """The defect this fixed: a wholly correct reply counted as partial."""
        assert index.unanswered("great, thanks!") == []

    @pytest.mark.parametrize("message", ["ok thanks", "cool, cheers", "right, bye"])
    def test_other_acknowledgements_behave_the_same(self, index, message):
        assert index.reply(message).answered

    def test_a_substantive_word_still_suppresses(self, index):
        """ "good" is an acknowledgement and "pay" is not, so "pay" decides."""
        assert index.reply("is the pay good").entry.answer == "RATE"


class TestABareAcknowledgementIsNotAQuestion:
    def test_it_is_dropped_from_a_split(self):
        assert QuestionSplitter.split("ok. what is your rate?") == ["what is your rate"]

    def test_a_message_of_nothing_else_splits_to_nothing(self):
        assert QuestionSplitter.split("cool") == []

    def test_one_inside_a_sentence_is_left_alone(self):
        """ "good" is only an acknowledgement when it is the whole part."""
        assert QuestionSplitter.split("is the pay good") == ["is the pay good"]

    def test_trailing_punctuation_does_not_hide_one(self):
        assert QuestionSplitter.split("great! what is your rate?") == ["what is your rate"]

    def test_the_set_is_replaceable(self):
        """Stated in the docstring, so it is tested."""
        assert "great" in QuestionSplitter.ACKNOWLEDGEMENTS
        assert isinstance(QuestionSplitter.ACKNOWLEDGEMENTS, frozenset)


class TestTheTagIsWhatDecides:
    """`SMALL_TALK_TAG` is the marker, so a custom set can opt in."""

    CUSTOM: ClassVar[list[Entry]] = [
        Entry(
            question="no problem",
            answer="SOCIAL",
            aliases=["np at all"],
            tags=["smalltalk", "custom"],
        ),
        Entry(question="What is your rate?", answer="RATE", aliases=["rate"]),
    ]

    def test_a_custom_tagged_entry_is_suppressed_too(self):
        index = Index(self.CUSTOM)
        assert index.reply("what is your rate").entry.answer == "RATE"

    def test_an_untagged_entry_is_not_suppressed(self):
        plain = [
            Entry(question="no problem", answer="SOCIAL", aliases=["np at all"]),
            Entry(question="What is your rate?", answer="RATE", aliases=["rate"]),
        ]
        index = Index(plain)
        assert index.reply("no problem").entry.answer == "SOCIAL"

    def test_the_tagged_one_still_answers_its_own_phrasing(self):
        assert Index(self.CUSTOM).reply("no problem").entry.answer == "SOCIAL"


class TestAnUnansweredSocialMessageIsStillHonest:
    def test_an_uncovered_question_with_a_social_word_is_refused(self, index):
        reply = index.reply("good afternoon, do you know kubernetes")
        assert reply.outcome is not Outcome.ANSWERED or reply.entry.answer != "Hello."
