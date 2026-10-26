"""A bare acknowledgement is not a question."""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index, QuestionSplitter, SmallTalk
from tests.social.small_talk_stays_in_its_lane import REPLIES


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
