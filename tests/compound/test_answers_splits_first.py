"""Answers splits first."""

from __future__ import annotations

import pytest

from lexmatch import Index
from tests.compound.a_message_asking_several_things import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestAnswersSplitsFirst:
    def test_each_part_scores_as_if_asked_alone(self, index):
        found = index.answers("remote? rates? notice period?")
        assert len(found) == 3
        for _, score in found:
            assert score > 0.9, "each part should score as a standalone question"

    def test_the_order_asked_is_kept(self, index):
        found = index.answers("remote? rates? notice period?")
        assert [entry.answer for entry, _ in found] == [
            "Yes, six years of it.",
            "It depends on scope.",
            "One month.",
        ]

    def test_a_single_question_behaves_as_before(self, index):
        found = index.answers("what are your rates")
        assert len(found) == 1
        assert found[0][0].answer == "It depends on scope."

    def test_nothing_answerable_gives_an_empty_list(self, index):
        """The same thing `answer()` reports with None."""
        assert index.answers("what is the weather and who won the match?") == []

    def test_duplicates_are_collapsed(self, index):
        """Two questions with one answer; saying it twice reads as a fault."""
        found = index.answers("rates? pricing?")
        assert len(found) == 1

    def test_it_answers_what_it_can(self, index):
        found = index.answers("what are your rates and what is your favourite film?")
        assert len(found) == 1
        assert found[0][0].answer == "It depends on scope."
