"""One sentence out of several answers, or out of none.

Assembling the reply was the same code in every application, and written
badly — the cases are not obvious until you have hit them. Three answers run
together with no connective read as a dump; a missed question left
unmentioned reads as having been understood; an ambiguous question answered
at all reads as a guess.
"""

from __future__ import annotations

import pytest

from lexmatch import Composer, Entry, Index, Outcome, Reply

ENTRIES = [
    Entry(
        question="What is your rate for design work?",
        answer="Design is £600 a day.",
        aliases=["design rate"],
    ),
    Entry(
        question="What is your rate for review work?",
        answer="Review is £500 a day.",
        aliases=["review rate"],
    ),
    Entry(
        question="What is your notice period?",
        answer="I need one month's notice.",
        aliases=["availability"],
    ),
    Entry(
        question="Are you open to remote work?",
        answer="Yes, I have worked remotely for six years",
        aliases=["remote"],
    ),
]


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestOneAnswer:
    def test_it_is_the_answer(self, index):
        assert index.respond("design rate?") == "Design is £600 a day."

    def test_punctuation_is_added_when_missing(self, index):
        """An answer without a full stop runs into the next one and the pair
        reads as a single sentence meaning something else."""
        assert index.respond("remote?").endswith(".")

    def test_the_owners_wording_is_otherwise_untouched(self, index):
        assert "I have worked remotely for six years" in index.respond("remote?")


class TestSeveralAnswers:
    def test_each_answer_appears(self, index):
        said = index.respond("remote? and notice period?")
        assert "remotely for six years" in said
        assert "one month's notice" in said

    def test_the_last_takes_a_connective(self, index):
        """Three statements adjacent read as a dump; a connective makes them
        a list."""
        assert "And " in index.respond("remote? and notice period?")

    def test_the_word_after_the_connective_is_lower_cased(self, index):
        """ "And Yes, I have" reads wrong."""
        said = index.respond("notice period? and remote?")
        assert "And yes" in said
        assert "And Yes" not in said

    def test_the_order_asked_is_the_order_answered(self, index):
        said = index.respond("notice period? and design rate?")
        assert said.index("one month") < said.index("£600")


class TestWhatWasMissed:
    def test_it_is_named(self, index):
        said = index.respond("design rate and what is your favourite film?")
        assert "favourite film" in said

    def test_the_question_reads_as_a_topic(self, index):
        """Quoted whole it reads as a transcript of the input rather than as
        part of a reply."""
        said = index.respond("design rate and what is your favourite film?")
        assert "about your favourite film" in said
        assert "what is your favourite film" not in said

    def test_several_misses_are_joined(self, index):
        said = index.respond("remote? and what are your hobbies? and do you have a dog?")
        assert " and " in said
        assert "answers about" in said, "plural when there are several"

    def test_one_miss_is_singular(self, index):
        said = index.respond("design rate and what is your favourite film?")
        assert "an answer about" in said

    def test_an_unrecognized_opening_is_quoted_as_it_came(self, index):
        """A slightly stiff sentence beats a mangled one."""
        assert Composer._as_topic("xyzzy plugh frobnicate?") == "xyzzy plugh frobnicate"

    def test_an_unanswerable_fragment_after_a_bare_and_is_not_reported(self, index):
        """The conservative side of a deliberate trade.

        "design rate and xyzzy" splits loosely into two parts, one
        answerable — but the loose reading is only preferred when it finds
        strictly *more answers*, and here it finds the same one. So the
        strict reading survives, the message counts as one question, and the
        fragment is not reported as missed.

        Measured, the alternative is worse. Preferring the loose split on
        equal answers would report "hybrid work" as unanswered in "are you
        open to remote and hybrid work" and "review work" in "do you do
        design and review work" — both of which *were* answered. A spurious
        "I don't know about that" on a question the bot just answered reads
        worse than quietly not mentioning a fragment nobody could answer.
        """
        said = index.respond("design rate and xyzzy plugh frobnicate?")
        assert said == "Design is £600 a day."

    def test_a_question_mark_does_report_it(self, index):
        """A terminator is unambiguous, so the fragment is a question and the
        miss is reported."""
        said = index.respond("design rate? xyzzy plugh frobnicate?")
        assert "xyzzy plugh frobnicate" in said


class TestTheOtherOutcomes:
    def test_ambiguity_asks_which(self, index):
        said = index.respond("what is your rate")
        assert said.startswith("Which did you mean")
        assert "design" in said
        assert "review" in said

    def test_the_options_lose_their_question_marks(self, index):
        """Or the sentence ends in "??"."""
        assert "??" not in index.respond("what is your rate")

    def test_a_negative_question_is_hedged(self, index):
        said = index.respond("are you not open to remote work")
        assert "rephrase" in said
        assert "Yes" not in said, "it must not answer the opposite"

    def test_nothing_matched_offers_suggestions(self, index):
        said = index.respond("what is the weather")
        assert "don't have an answer" in said
        assert "You could try" in said

    def test_an_empty_index_says_so_without_suggestions(self):
        assert Index([]).respond("anything") == Composer.NOTHING


class TestAnswersGoesThroughReply:
    """Using the simpler `answer()` bypassed every check `reply()` exists
    for, on exactly the messages most likely to need them."""

    def test_an_ambiguous_part_is_not_answered(self, index):
        """ "what is your rate" inside a compound message must not be
        answered with the first of its contenders."""
        said = index.respond("what is your rate and are you remote?")
        assert "£600" not in said or "Which did you mean" in said

    def test_a_negative_part_is_not_answered(self, index):
        said = index.respond("design rate and are you not open to remote work?")
        assert "remotely for six years" not in said


class TestAVoiceOfYourOwn:
    def test_a_phrase_can_be_replaced(self, index):
        class Warmer(Composer):
            NOTHING = "Hmm, that one's new to me."

        warm = Index(ENTRIES, composer=Warmer)
        assert warm.respond("what is the weather").startswith("Hmm, that one's new")

    def test_the_sequencing_is_kept(self, index):
        class Warmer(Composer):
            AND = "Also, "

        warm = Index(ENTRIES, composer=Warmer)
        said = warm.respond("notice period? and remote?")
        assert "Also, yes" in said

    def test_the_missed_template_takes_the_questions(self):
        class Warmer(Composer):
            MISSED_ONE = "No idea about {questions}!"

        warm = Index(ENTRIES, composer=Warmer)
        said = warm.respond("design rate and what is your favourite film?")
        assert "No idea about your favourite film!" in said

    def test_the_default_is_used_when_none_is_given(self, index):
        assert index.respond("what is the weather").startswith(Composer.NOTHING)


class TestNothingIsInvented:
    """Every sentence is an entry's own answer or one of Composer's phrases,
    so a response can say nothing the owner did not write."""

    def test_every_word_comes_from_somewhere(self, index):
        said = index.respond("design rate and what is your favourite film?")
        from_entries = " ".join(entry.answer for entry in ENTRIES)
        known = (
            set(from_entries.lower().split())
            | set(Composer.MISSED_ONE.lower().replace("{questions}", "").split())
            | {"your", "favourite", "film,"}
        )
        for word in said.lower().split():
            assert word in known or word.strip(".,!?") in {w.strip(".,!?") for w in known}, (
                f"{word!r} appeared from nowhere"
            )


class TestTheComposerDirectly:
    """Shapes `respond()` never produces, but a caller using the composer on
    its own will."""

    def test_no_answers_and_no_misses_says_nothing_found(self):
        assert Composer.compose([], []) == Composer.NOTHING

    def test_no_answers_but_misses_offers_them(self):
        said = Composer.compose([], ["what is your favourite film"])
        assert "You could try" in said
        assert "your favourite film" in said

    def test_a_compose_reply_of_an_answered_reply(self):
        entry = Entry(question="q", answer="An answer")
        reply = Reply(outcome=Outcome.ANSWERED, entry=entry, score=1.0)
        assert Composer.compose_reply(reply) == "An answer."

    def test_a_compose_reply_with_no_entry_falls_through(self):
        """An ANSWERED outcome with no entry should not be possible, and the
        composer still has to say something rather than raise."""
        assert Composer.compose_reply(Reply(outcome=Outcome.ANSWERED)) == Composer.NOTHING

    def test_two_items_join_with_and_and_no_comma(self):
        assert Composer._join(["a", "b"]) == "a and b"

    def test_three_items_take_commas_and_a_final_and(self):
        assert Composer._join(["a", "b", "c"]) == "a, b and c"

    def test_one_item_stands_alone(self):
        assert Composer._join(["a"]) == "a"

    def test_an_empty_answer_is_not_given_a_full_stop(self):
        assert Composer._sentence("   ") == ""

    def test_existing_punctuation_is_kept(self):
        for text in ("Yes!", "Really?", "Done.", "Wait…"):
            assert Composer._sentence(text) == text

    def test_a_capital_after_a_connective_is_kept_when_it_is_an_initialism(self):
        """ "And NDAs are fine" keeps its capital; "And Yes" does not."""
        assert Composer._lower_first("NDAs are fine") == "NDAs are fine"
        assert Composer._lower_first("Yes, of course") == "yes, of course"

    def test_a_single_character_is_left_alone(self):
        assert Composer._lower_first("A") == "A"
