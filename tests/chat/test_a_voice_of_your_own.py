"""A voice of your own."""

from __future__ import annotations

import pytest

from lexmatch import Composer, Index
from tests.chat.composing_a_reply import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


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
