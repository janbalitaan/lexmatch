"""An alias is optional by nature, so a blank one is dropped rather than
refused — a trailing empty column is what a spreadsheet export looks
like, and dropping one costs nothing."""

from __future__ import annotations

from lexmatch import Entry


class TestWhatIsForgivenInstead:
    """An alias is optional by nature, so a blank one is dropped rather than
    refused — a trailing empty column is what a spreadsheet export looks
    like, and dropping one costs nothing."""

    def test_blank_aliases_are_dropped(self):
        entry = Entry(question="What do you do?", answer="A.", aliases=["", "  ", "job"])
        assert entry.aliases == ["job"]

    def test_blank_tags_are_dropped(self):
        entry = Entry(question="What do you do?", answer="A.", tags=["", "work"])
        assert entry.tags == ["work"]

    def test_an_entry_of_only_blank_aliases_still_builds(self):
        entry = Entry(question="What do you do?", answer="A.", aliases=["", ""])
        assert entry.aliases == []
