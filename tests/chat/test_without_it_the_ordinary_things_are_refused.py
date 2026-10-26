"""The gap it closes."""

from __future__ import annotations

import pytest

from lexmatch import Index, SmallTalk
from tests.chat.small_talk import CONTENT, REPLIES


@pytest.fixture
def index() -> Index:
    return Index([*SmallTalk.entries(REPLIES), *CONTENT])


class TestWithoutItTheOrdinaryThingsAreRefused:
    """The gap it closes."""

    @pytest.mark.parametrize("message", ["hi", "thanks!", "who are you", "bye"])
    def test_a_bare_index_refuses(self, message):
        assert Index(CONTENT).answer(message)[0] is None
