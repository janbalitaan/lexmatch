"""Saying what was missed."""

from __future__ import annotations

import pytest

from lexmatch import Index, QuestionSplitter
from tests.compound.a_message_asking_several_things import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestSayingWhatWasMissed:
    def test_unanswered_names_the_question(self, index):
        missed = index.unanswered("what are your rates and what is your favourite film?")
        assert missed == ["what is your favourite film"]

    def test_it_is_empty_when_everything_answered(self, index):
        assert index.unanswered("remote? rates?") == []

    def test_together_they_account_for_the_whole_message(self, index):
        message = "remote? rates? what is the weather?"
        answered = len(index.answers(message))
        missed = len(index.unanswered(message))
        assert answered + missed == len(QuestionSplitter.split(message))
