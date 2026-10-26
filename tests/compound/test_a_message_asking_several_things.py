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

from typing import ClassVar

import pytest

from lexmatch import Entry, Index, Outcome, QuestionSplitter, SmallTalk

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
        """The arithmetic, demonstrated rather than asserted.

        Each part is diluted by the others, so no part scores what it would
        have scored alone. How far it falls has moved with the scorer — the
        second part used to drop below the threshold and now clears it — so
        what is asserted is the dilution itself, not a particular depth.
        """
        whole = index.score("remote? rates? notice period?")
        alone = index.score("remote")[0][0]
        assert whole[0][0] < alone, (
            f"asking three things at once scored {whole[0][0]:.3f}, no worse "
            f"than asking one ({alone:.3f}) — the dilution is the premise"
        )
        assert whole[1][0] < whole[0][0]
        assert whole[2][0] < whole[1][0]


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


class TestTheStrictReadingSurvivesWhenLooseGainsNothing:
    """The loose split is a second opinion, discarded unless it finds more.

    "are you open to remote and hybrid work" splits loosely into two halves
    that answer the same entry — so the loose reading finds the same single
    answer, gains nothing, and the strict reading is kept. Keeping the loose
    one would report "hybrid work" as unanswered on a question that *was*
    answered.
    """

    SHARED: ClassVar[list[Entry]] = [
        Entry(question="Are you open to remote and hybrid work?", answer="Both.", aliases=[]),
        Entry(
            question="What is your notice period?",
            answer="One month.",
            aliases=["availability"],
        ),
    ]

    def test_the_whole_question_is_answered(self):
        index = Index(self.SHARED)
        found = index.answers("are you open to remote and hybrid work?")
        assert len(found) == 1
        assert found[0][0].answer == "Both."

    def test_nothing_is_reported_as_missed(self):
        index = Index(self.SHARED)
        assert index.unanswered("are you open to remote and hybrid work?") == []

    def test_the_loose_split_really_would_have_split_it(self):
        """So the test is exercising the discard rather than a split that
        never happened."""
        assert (
            len(QuestionSplitter.split_loosely("are you open to remote and hybrid work?")) == 2
        )
        assert len(QuestionSplitter.split("are you open to remote and hybrid work?")) == 1

    def test_and_the_loose_one_wins_when_it_does_find_more(self):
        """ "remote and notice period" has no interrogative after the "and",
        so the strict rule keeps it whole and answers one of the two. The
        loose rule answers both, which is the evidence that they were
        separate questions."""
        index = Index(self.SHARED)
        strict = QuestionSplitter.split("remote and notice period")
        loose = QuestionSplitter.split_loosely("remote and notice period")
        assert len(strict) == 1, "the premise: the strict rule keeps it whole"
        assert len(loose) == 2
        assert len(index.answers("remote and notice period")) == 2


class TestAMessageThatAsksTwoThingsIsNotAmbiguous:
    """Ambiguity is one question matching two entries.

    Two questions matching one entry each is not that, and asking which was
    meant answers neither. Measured: "yoe and tech stack?" tied at 0.586
    between the experience and stack entries and asked which was meant,
    while `answers()` on the same message had already resolved it to both —
    `reply()` scored the whole string and never consulted the reading.
    """

    PAIR: ClassVar[list[Entry]] = [
        Entry(
            question="How many years of experience?",
            answer="YEARS",
            aliases=["yoe", "experience"],
        ),
        Entry(
            question="What is your tech stack?", answer="STACK", aliases=["tech stack", "stack"]
        ),
        Entry(question="What is your notice period?", answer="NOTICE", aliases=["notice"]),
        Entry(question="What are your rates?", answer="RATE", aliases=["rate"]),
    ]

    def test_it_is_answered_not_reported_ambiguous(self):
        reply = Index(self.PAIR).reply("yoe and tech stack?")
        assert reply.outcome is Outcome.ANSWERED

    def test_both_answers_are_carried(self):
        reply = Index(self.PAIR).reply("yoe and tech stack?")
        found = {reply.entry.answer, *(entry.answer for entry in reply.alternatives)}
        assert found == {"YEARS", "STACK"}

    def test_a_genuinely_ambiguous_question_is_still_ambiguous(self):
        """One question, two entries — which is what ambiguity means."""
        rates = [
            Entry(question="What is your rate for design work?", answer="DESIGN"),
            Entry(question="What is your rate for review work?", answer="REVIEW"),
            Entry(question="What is your notice period?", answer="NOTICE", aliases=["notice"]),
            Entry(question="Are you open to remote work?", answer="REMOTE", aliases=["remote"]),
            Entry(question="Do you need visa sponsorship?", answer="VISA", aliases=["visa"]),
            Entry(question="What is your tech stack?", answer="STACK", aliases=["stack"]),
        ]
        assert Index(rates).reply("what is your rate").outcome is Outcome.AMBIGUOUS


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
