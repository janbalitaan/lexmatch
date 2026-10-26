"""Using the simpler `answer()` bypassed every check `reply()` exists
for, on exactly the messages most likely to need them."""

from __future__ import annotations

import pytest

from lexmatch import Index
from tests.chat.composing_a_reply import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


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
