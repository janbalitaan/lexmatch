"""A message that asks more than one thing.

`answer()` treats the whole message as one question, and a compound message
then scores *worse* against every entry than any one part would alone — the
phrase measure is an overlap ratio, so doubling the query's length halves the
proportion any single entry can share.

Measured on "remote? rates? notice period?" the best entry reached 0.480 and
the other two 0.400 and 0.250, both under the threshold. One answer, two
silent omissions, and nothing saying so.
"""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index, QuestionSplitter

ENTRIES = [
    Entry(
        question="Are you open to remote work?",
        answer="Yes, six years of it.",
        aliases=["remote", "work from home", "wfh"],
    ),
    Entry(
        question="What are your rates?",
        answer="It depends on scope.",
        aliases=["pricing", "day rate", "how much"],
    ),
    Entry(
        question="What is your notice period?",
        answer="One month.",
        aliases=["when can you start", "availability"],
    ),
]


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestTheProblemAnswersSolves:
    def test_answer_replies_to_only_one_part(self, index):
        replies = index.answer("are you remote and what are your rates?")
        assert replies[0] is not None
        assert len(index.answers("are you remote and what are your rates?")) == 2

    def test_a_three_part_message_degrades_every_score(self, index):
        """The arithmetic, demonstrated rather than asserted."""
        whole = index.score("remote? rates? notice period?")
        assert whole[0][0] < 0.5, "the best score should have degraded"
        assert whole[1][0] < index.threshold, "the second should fall below"
        assert whole[2][0] < index.threshold, "and the third"


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
