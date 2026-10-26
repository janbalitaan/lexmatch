"""Hello, thanks, who are you.

A bot that refuses "thanks!" reads as broken in a way that a bot refusing an
obscure question does not: the visitor knows they said something ordinary, so
the failure looks like the bot rather than like the question.
"""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index, SmallTalk
from lexmatch.exceptions import SmallTalkError

REPLIES = {
    "greeting": "Hello. Ask me anything about Jan's work.",
    "thanks": "You're welcome.",
    "farewell": "Take care.",
    "identity": "I'm a small bot that answers questions about Jan.",
    "capability": "Try asking about remote work or rates.",
    "wellbeing": "Well, thanks.",
}
CONTENT = [
    Entry(question="Are you open to remote work?", answer="Yes.", aliases=["remote"]),
    Entry(question="What are your rates?", answer="It depends.", aliases=["pricing"]),
]


@pytest.fixture
def index() -> Index:
    return Index([*SmallTalk.entries(REPLIES), *CONTENT])


class TestWithoutItTheOrdinaryThingsAreRefused:
    """The gap it closes."""

    @pytest.mark.parametrize("message", ["hi", "thanks!", "who are you", "bye"])
    def test_a_bare_index_refuses(self, message):
        assert Index(CONTENT).answer(message)[0] is None


class TestTheConversationalTurnsAnswer:
    @pytest.mark.parametrize(
        ("message", "expected"),
        [
            ("hi", "greeting"),
            ("hello", "greeting"),
            ("hey there", "greeting"),
            ("good morning", "greeting"),
            ("thanks", "thanks"),
            ("thanks!", "thanks"),
            ("cheers", "thanks"),
            ("much appreciated", "thanks"),
            ("bye", "farewell"),
            ("take care", "farewell"),
            ("who are you", "identity"),
            ("are you a bot", "identity"),
            ("are you human", "identity"),
            ("what can i ask", "capability"),
            ("help", "capability"),
            ("how are you", "wellbeing"),
        ],
    )
    def test_it_reaches_the_right_intent(self, index, message, expected):
        entry, score = index.answer(message)
        assert entry is not None, f"{message!r} refused at {score:.3f}"
        assert entry.answer == REPLIES[expected], f"{message!r} -> {entry.answer!r}"

    def test_content_questions_still_work(self, index):
        """Small talk must not crowd out the real entries."""
        assert index.answer("remote?")[0].answer == "Yes."
        assert index.answer("pricing")[0].answer == "It depends."

    def test_an_unrelated_question_is_still_refused(self, index):
        """Adding small talk must not make the index answer everything."""
        assert index.answer("what is the weather")[0] is None


class TestOnlyTheRepliesYouGive:
    def test_an_intent_without_a_reply_is_not_added(self):
        entries = SmallTalk.entries({"greeting": "Hello."})
        assert len(entries) == 1
        assert Index(entries).answer("thanks")[0] is None

    def test_an_empty_reply_is_skipped(self):
        assert SmallTalk.entries({"greeting": "Hello.", "thanks": "   "}) == [
            *SmallTalk.entries({"greeting": "Hello."})
        ]

    def test_nothing_given_builds_nothing(self):
        assert SmallTalk.entries({}) == []

    def test_an_unknown_intent_raises(self):
        """A typo leaves the handler silently absent, which looks exactly
        like one that works until somebody says hello."""
        with pytest.raises(SmallTalkError, match="no such small-talk intent"):
            SmallTalk.entries({"greetings": "Hello."})

    def test_the_message_lists_what_is_available(self):
        with pytest.raises(SmallTalkError, match="greeting"):
            SmallTalk.entries({"nope": "Hello."})


class TestItStaysOutOfTheSuggestions:
    """Offering "hello" to somebody whose question could not be answered
    reads as not having understood that they asked a question."""

    def test_suggestions_are_content_only(self, index):
        assert index.suggestions(limit=5) == [
            "Are you open to remote work?",
            "What are your rates?",
        ]

    def test_an_index_of_small_talk_alone_still_suggests(self):
        index = Index(SmallTalk.entries({"greeting": "Hello."}))
        assert index.suggestions(limit=2) == ["hello"]

    def test_the_tag_is_what_marks_them(self):
        entry = SmallTalk.entries({"greeting": "Hello."})[0]
        assert "smalltalk" in entry.tags
        assert "greeting" in entry.tags


class TestExtendingThePhrasings:
    def test_the_phrasings_are_available(self):
        assert "hiya" in SmallTalk.phrasings_for("greeting")

    def test_an_unknown_intent_raises(self):
        with pytest.raises(SmallTalkError, match="no such small-talk intent"):
            SmallTalk.phrasings_for("nope")

    def test_the_intents_are_listed(self):
        assert "greeting" in SmallTalk.INTENTS
        assert len(SmallTalk.INTENTS) == 6

    def test_a_caller_can_build_on_them(self):
        phrasings = SmallTalk.phrasings_for("greeting")
        entry = Entry(
            question=phrasings[0],
            answer="Aloha!",
            aliases=[*phrasings[1:], "aloha", "salut"],
        )
        assert Index([entry]).answer("salut")[0] is not None
        assert Index([entry]).answer("hiya")[0] is not None
