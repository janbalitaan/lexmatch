"""Every sentence is an entry's own answer or one of Composer's phrases,
so a response can say nothing the owner did not write."""

from __future__ import annotations

import pytest

from lexmatch import Composer, Index
from tests.chat.composing_a_reply import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


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
