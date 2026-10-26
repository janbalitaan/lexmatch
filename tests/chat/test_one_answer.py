"""One answer."""

from __future__ import annotations

import pytest

from lexmatch import Index
from tests.chat.composing_a_reply import ENTRIES


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
