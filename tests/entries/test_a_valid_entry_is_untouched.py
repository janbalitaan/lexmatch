"""A valid entry is untouched."""

from __future__ import annotations

from lexmatch import Entry, EntryError, LexmatchError


class TestAValidEntryIsUntouched:
    def test_it_builds(self):
        entry = Entry(
            question="Are you open to remote work?",
            answer="Yes.",
            aliases=["remote"],
            tags=["logistics"],
        )
        assert entry.question == "Are you open to remote work?"
        assert entry.aliases == ["remote"]
        assert entry.tags == ["logistics"]

    def test_the_error_is_a_lexmatch_error(self):
        """So one `except` catches everything from this library."""
        assert issubclass(EntryError, LexmatchError)
