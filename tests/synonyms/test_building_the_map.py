"""Building the map."""

from __future__ import annotations

import pytest

from lexmatch import Synonyms
from lexmatch.exceptions import SynonymError


class TestBuildingTheMap:
    def test_a_phrase_value_is_split(self):
        assert Synonyms.of({"wfh": "work from home"}).mapping["wfh"] == (
            "work",
            "from",
            "home",
        )

    def test_a_list_value_works_too(self):
        assert Synonyms.of({"wfh": ["work", "from", "home"]}).mapping["wfh"] == (
            "work",
            "from",
            "home",
        )

    def test_keys_are_lower_cased(self):
        """Matching is on normalized tokens, so a capitalized key would look
        like it worked while matching nothing."""
        assert "wfh" in Synonyms.of({"WFH": "work from home"}).mapping

    def test_values_are_lower_cased(self):
        assert Synonyms.of({"wfh": "Work From Home"}).mapping["wfh"] == (
            "work",
            "from",
            "home",
        )

    def test_a_phrase_key_is_accepted(self):
        """It used to be refused, on the grounds that expansion happened one
        token at a time. That was a statement about the implementation
        rather than a constraint, and `{"how much": "rate"}` is the one
        thing neither stopwords nor single-word synonyms can bridge."""
        synonyms = Synonyms.of({"how much": "rate"})
        assert synonyms.mapping["how much"] == ("rate",)
        assert synonyms.longest_key == 2

    def test_a_phrase_is_matched_across_tokens(self):
        synonyms = Synonyms.of({"how much": "rate"})
        assert synonyms.expand(["how", "much", "for", "design"]) == [
            "how",
            "much",
            "rate",
            "for",
            "design",
        ]

    def test_the_longest_phrase_wins(self):
        """A map holding both "how much" and "much" has to read the pair as
        the pair, or the longer entry could never fire — the same silent
        failure as refusing it outright."""
        synonyms = Synonyms.of({"how much": "rate", "much": "lots"})
        assert synonyms.expand(["how", "much"]) == ["how", "much", "rate"]
        assert synonyms.expand(["much", "later"]) == ["much", "lots", "later"]

    def test_a_phrase_that_does_not_appear_changes_nothing(self):
        synonyms = Synonyms.of({"how much": "rate"})
        assert synonyms.expand(["how", "are", "you"]) == ["how", "are", "you"]

    def test_a_single_word_map_needs_no_lookahead(self):
        assert Synonyms.of({"wfh": "remote"}).longest_key == 1

    def test_an_empty_map_reports_a_window_of_one(self):
        assert Synonyms().longest_key == 1

    def test_an_empty_key_is_refused(self):
        with pytest.raises(SynonymError, match="cannot be empty"):
            Synonyms.of({"": "remote"})

    def test_a_value_that_expands_to_nothing_is_refused(self):
        with pytest.raises(SynonymError, match="expands to nothing"):
            Synonyms.of({"wfh": "   "})

    def test_with_pairs_adds_to_what_is_there(self):
        first = Synonyms.of({"wfh": "work from home"})
        both = first.with_pairs({"comp": "compensation"})
        assert set(both.mapping) == {"wfh", "comp"}

    def test_a_repeated_key_takes_the_later_value(self):
        first = Synonyms.of({"comp": "compensation"})
        later = first.with_pairs({"comp": "company"})
        assert later.mapping["comp"] == ("company",)
