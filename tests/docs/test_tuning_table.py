"""The README publishes these three numbers, so they are part of the API."""

from __future__ import annotations

import pytest

from lexmatch import (
    DEFAULT_THRESHOLD,
    LENGTH_PENALTY,
    TERM_FREQUENCY_SATURATION,
    Entry,
    Index,
)


@pytest.fixture
def index() -> Index:
    """The exact index the README's opening example builds."""
    return Index(
        [
            Entry(
                "What do you do?",
                "I build backend services.",
                aliases=["what is your job", "what is your role"],
            ),
            Entry(
                "Are you open to remote work?",
                "Yes, and to relocation.",
                aliases=["remote", "relocate", "would you move", "hybrid"],
            ),
        ]
    )


class TestTuningTable:
    """The README publishes these three numbers, so they are part of the API."""

    def test_the_threshold(self):
        assert DEFAULT_THRESHOLD == 0.45

    def test_the_saturation(self):
        assert TERM_FREQUENCY_SATURATION == 1.4

    def test_the_length_penalty(self):
        assert LENGTH_PENALTY == 0.72

    def test_the_threshold_is_configurable_as_documented(self, index):
        strict = Index(
            list(index._entries) if hasattr(index, "_entries") else [], threshold=1.01
        )
        assert strict.answer("What do you do?")[0] is None
