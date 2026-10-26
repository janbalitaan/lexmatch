"""What was missed."""

from __future__ import annotations

import pytest

from lexmatch import Composer, Index
from tests.chat.composing_a_reply import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


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
