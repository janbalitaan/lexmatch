"""Expanding."""

from __future__ import annotations

from lexmatch import Synonyms


class TestExpanding:
    def test_an_unknown_token_is_untouched(self):
        synonyms = Synonyms.of({"wfh": "work from home"})
        assert synonyms.expand(["rates"]) == ["rates"]

    def test_an_empty_map_changes_nothing(self):
        assert Synonyms().expand(["a", "b"]) == ["a", "b"]

    def test_the_expansion_follows_the_original(self):
        synonyms = Synonyms.of({"wfh": "work from home"})
        assert synonyms.expand(["wfh"]) == ["wfh", "work", "from", "home"]

    def test_order_is_preserved(self):
        synonyms = Synonyms.of({"wfh": "remote"})
        assert synonyms.expand(["do", "wfh", "please"]) == [
            "do",
            "wfh",
            "remote",
            "please",
        ]
