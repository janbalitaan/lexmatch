"""Shapes `respond()` never produces, but a caller using the composer on
its own will."""

from __future__ import annotations

import pytest

from lexmatch import Composer, Entry, Index, Outcome, Reply
from tests.chat.composing_a_reply import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


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
        # A real question, not a placeholder: a one-character question
        # normalizes to nothing and `Entry` refuses it, because no query
        # could ever match it.
        entry = Entry(question="What do you do?", answer="An answer")
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
