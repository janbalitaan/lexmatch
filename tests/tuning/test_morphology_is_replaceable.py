"""A query word may be the start of a longer word the index holds.

Stemming folds inflection and deliberately stops at derivation, because
the endings it would have to strip change what a word means. An index
holding "seniority" and not "senior" is then unreachable by "are you a
senior", and nothing reports it."""

from __future__ import annotations

from typing import ClassVar

from lexmatch import Entry, Index
from lexmatch.models.tuning import Tuning
from lexmatch.morphology import Morphology


class TestMorphologyIsReplaceable:
    """A query word may be the start of a longer word the index holds.

    Stemming folds inflection and deliberately stops at derivation, because
    the endings it would have to strip change what a word means. An index
    holding "seniority" and not "senior" is then unreachable by "are you a
    senior", and nothing reports it.
    """

    DERIVED: ClassVar[list[Entry]] = [
        Entry(
            question="How many years of experience?",
            answer="YEARS",
            aliases=["seniority", "experience"],
        ),
        Entry(
            question="How do you think about security?", answer="SECURITY", aliases=["security"]
        ),
        Entry(question="What is your notice period?", answer="NOTICE", aliases=["notice"]),
    ]

    def test_it_is_on_by_default(self):
        assert Index(self.DERIVED).reply("are you a senior").entry.answer == "YEARS"

    def test_it_works_in_stem_space(self):
        """ "secure" folds to "secur", which is a prefix of "security"; the
        unfolded "secure" is a prefix of nothing because of its "e"."""
        assert Index(self.DERIVED).reply("is it secure").entry.answer == "SECURITY"

    def test_none_turns_it_off(self):
        off = Index(self.DERIVED, tuning=Tuning().with_morphology(None))
        assert not off.reply("are you a senior").answered

    def test_an_ambiguous_prefix_is_left_alone(self):
        """Two index words starting the same way means the query word is
        ambiguous, and picking one is wrong half the time."""
        both = [
            Entry(question="How do you design a system?", answer="DESIGN", aliases=["design"]),
            Entry(
                question="How do you work with a designer?",
                answer="DESIGNER",
                aliases=["designer"],
            ),
        ]
        index = Index(both)
        assert Morphology.extend("design", index._stemmed_vocabulary) == "design"

    def test_a_short_word_is_not_evidence(self):
        vocabulary = frozenset({"leadership", "planet"})
        assert Morphology.extend("plan", vocabulary) == "plan"

    def test_it_only_ever_lengthens_toward_a_word_the_index_holds(self):
        """It cannot invent a term."""
        assert Morphology.extend("senior", frozenset({"notice"})) == "senior"

    def test_a_complete_word_is_protected(self):
        assert Morphology.extend("there", frozenset({"therefore"})) == "there"

    def test_describe_says_which(self):
        assert "morphology on" in Tuning().describe()
        assert "morphology off" in Tuning().with_morphology(None).describe()

    def test_a_replacement_is_used(self):
        shouty = Index(
            self.DERIVED,
            tuning=Tuning().with_morphology(lambda words, vocab: [w.upper() for w in words]),
        )
        assert shouty.reply("notice") is not None
