"""A word that means the same thing index-wide, declared once.

Aliases attach a phrasing to one entry. Writing `wfh` into the aliases of
every entry that mentions remote work is the same fact recorded five times,
and the fifth entry is the one somebody forgets.
"""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index, Synonyms, Tuning
from lexmatch.exceptions import SynonymError

ENTRIES = [
    Entry(question="Are you open to remote work?", answer="Yes."),
    Entry(question="What is your compensation expectation?", answer="Negotiable."),
]


class TestWithoutSynonymsAShortFormMisses:
    """The gap they close."""

    @pytest.mark.parametrize("query", ["wfh", "comp"])
    def test_it_scores_nothing(self, query):
        _, score = Index(ENTRIES).answer(query)
        assert score == 0.0

    def test_no_threshold_reaches_it(self):
        """There is no signal to find, so lowering the threshold cannot help."""
        assert Index(ENTRIES, threshold=0.01).answer("wfh")[0] is None


class TestWithSynonymsItMatches:
    @pytest.fixture
    def index(self) -> Index:
        return Index(
            ENTRIES,
            tuning=Tuning().with_synonyms({"wfh": "remote work", "comp": "compensation"}),
        )

    @pytest.mark.parametrize("query", ["wfh", "comp"])
    def test_the_short_form_answers(self, index, query):
        entry, score = index.answer(query)
        assert entry is not None, f"{query!r} still misses"
        assert score > 0

    def test_the_long_form_is_not_weakened(self, index):
        """Adding a synonym must not cost the word it expands to."""
        plain = Index(ENTRIES).answer("compensation")[1]
        tuned = index.answer("compensation")[1]
        assert abs(tuned - plain) < 0.001

    def test_the_original_token_is_kept(self):
        """So a short form still matches an entry that uses the short form."""
        entries = [Entry(question="What is the comp?", answer="Negotiable.")]
        index = Index(entries, tuning=Tuning().with_synonyms({"comp": "compensation"}))
        assert index.answer("comp")[0] is not None

    def test_both_sides_go_through_the_map(self):
        """A short form in the entry meets a long form in the query."""
        entries = [Entry(question="Do you do wfh?", answer="Yes.")]
        index = Index(entries, tuning=Tuning().with_synonyms({"wfh": "work from home"}))
        assert index.answer("work from home")[0] is not None


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

    def test_a_multi_word_key_is_refused(self):
        """Expansion is token by token, so it could never match — and a map
        that silently does nothing looks exactly like one that works."""
        with pytest.raises(SynonymError, match="more than one word"):
            Synonyms.of({"work from home": "remote"})

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


class TestDescribe:
    def test_it_counts_them(self):
        assert "2 synonyms" in Synonyms.of({"a": "b", "c": "d"}).describe()

    def test_it_appears_in_the_tuning_summary(self):
        described = Tuning().with_synonyms({"wfh": "remote"}).describe()
        assert "1 synonyms" in described

    def test_it_does_not_list_them(self):
        """Safe to log."""
        assert "wfh" not in Synonyms.of({"wfh": "remote"}).describe()
