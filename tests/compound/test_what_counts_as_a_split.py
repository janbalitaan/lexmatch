"""Conservative, because a wrong split answers a question nobody asked."""

from __future__ import annotations

import pytest

from lexmatch import Index, QuestionSplitter
from tests.compound.a_message_asking_several_things import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestWhatCountsAsASplit:
    """Conservative, because a wrong split answers a question nobody asked."""

    @pytest.mark.parametrize(
        ("message", "parts"),
        [
            ("are you remote and what are your rates?", 2),
            ("what are your rates and when can you start?", 2),
            ("remote? rates? notice period?", 3),
            ("what do you charge? Also, when can you start?", 2),
            ("rates; availability", 2),
            ("rates\navailability", 2),
        ],
    )
    def test_these_are_several_questions(self, message, parts):
        assert len(QuestionSplitter.split(message)) == parts

    @pytest.mark.parametrize(
        "message",
        [
            "are you open to remote and hybrid work?",
            "what is your rate and availability",
            "do you do design and review work",
            "what are your rates",
        ],
    )
    def test_these_are_one_question_about_two_things(self, message):
        assert len(QuestionSplitter.split(message)) == 1

    def test_a_word_before_a_question_mark_is_a_question(self):
        """An earlier version folded single words into their neighbour and
        turned "remote? rates?" into "remote rates", which means neither."""
        assert QuestionSplitter.split("remote? rates?") == ["remote", "rates"]

    @pytest.mark.parametrize("message", ["", "   ", "?", "???"])
    def test_nothing_askable_gives_nothing(self, message):
        assert QuestionSplitter.split(message) == []

    def test_looks_compound_agrees_with_split(self):
        assert QuestionSplitter.looks_compound("rates? availability?")
        assert not QuestionSplitter.looks_compound("what are your rates")
        assert not QuestionSplitter.looks_compound("")
