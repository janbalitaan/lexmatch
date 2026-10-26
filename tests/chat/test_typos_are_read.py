"""A mistyped word read as the word it is.

A lexical matcher refusing "whats your raets" reads as stupidity: a person
would answer without noticing. Neither aliases nor synonyms help, because a
misspelling is not a word anybody would think to declare.
"""

from __future__ import annotations

import pytest

from lexmatch import Corrections, Entry, Index, Tuning
from lexmatch.exceptions import TuningError

ENTRIES = [
    Entry(question="Are you open to remote work?", answer="Yes.", aliases=["remote"]),
    Entry(question="What are your rates?", answer="It depends.", aliases=["pricing"]),
    Entry(
        question="What is your notice period?", answer="One month.", aliases=["availability"]
    ),
]
VOCABULARY = frozenset(
    {"remote", "work", "rates", "notice", "period", "python", "senior", "junior", "rust"}
)


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestATypoIsAnswered:
    @pytest.mark.parametrize(
        "query", ["whats your raets", "remte work", "notce period", "availabilty", "pricng"]
    )
    def test_it_finds_an_answer(self, index, query):
        entry, score = index.answer(query)
        assert entry is not None, f"{query!r} still refused at {score:.3f}"

    @pytest.mark.parametrize("query", ["whats your raets", "pricng"])
    def test_it_was_refused_before(self, query):
        """The gap, stated so a regression is visible."""
        off = Index(ENTRIES, tuning=Tuning().with_corrections(enabled=False))
        assert off.answer(query)[0] is None

    @pytest.mark.parametrize("query", ["whats your raets", "pricng", "availabilty", "remte"])
    def test_a_refused_query_becomes_a_confident_one(self, query):
        """From nothing to a clear match.

        An earlier version of this test used "notce period", on the grounds
        that it scraped over the threshold on "period" alone and correction
        made it certain. It no longer scrapes: once BM25 was normalized
        against a *reachable* ceiling, one matching content word is already
        confident, so the before-and-after is 0.000 to ~1.000 or nothing.
        """
        off = Index(ENTRIES, tuning=Tuning().with_corrections(enabled=False))
        on = Index(ENTRIES)
        before = off.score(query)[0][0]
        after = on.score(query)[0][0]
        assert before == 0.0, f"{query!r} was not refused before: {before:.3f}"
        assert after > 0.9, f"{query!r} is not confident after: {after:.3f}"


class TestItNeverOverridesARealWord:
    """A word in the vocabulary is better evidence than any similarity."""

    @pytest.mark.parametrize("word", ["senior", "junior", "rust", "python", "remote"])
    def test_a_vocabulary_word_is_untouched(self, word):
        assert Corrections()._best(word, VOCABULARY) == word

    def test_an_unrelated_query_still_refuses(self, index):
        """Correction must not invent a match out of nothing."""
        for query in ("what is the weather", "who won the match", "xyzzy plugh"):
            assert index.answer(query)[0] is None, query


class TestTheGuards:
    def test_a_short_token_is_skipped(self):
        """Below four characters almost everything is one edit from
        everything, so "api" would correct to "and"."""
        assert Corrections()._best("api", frozenset({"and", "all"})) == "api"

    def test_the_similarity_bar_holds(self):
        """`rateing` is 0.667 similar to `rates`, under the 0.8 bar."""
        assert Corrections()._best("rateing", frozenset({"rates"})) == "rateing"

    def test_a_tie_is_left_alone(self):
        """Two equally close candidates means the word is ambiguous."""
        assert Corrections()._best("bat", frozenset({"cat", "rat"})) == "bat"

    def test_a_clear_winner_is_taken(self):
        assert Corrections()._best("desgin", frozenset({"design", "review"})) == "design"

    def test_length_spread_limits_the_candidates(self):
        """A token cannot be a typo of something far longer."""
        assert Corrections()._best("rate", frozenset({"rationalisation"})) == "rate"


class TestConfiguring:
    def test_it_can_be_turned_off(self):
        off = Index(ENTRIES, tuning=Tuning().with_corrections(enabled=False))
        assert off.answer("pricng")[0] is None
        assert Index(ENTRIES).answer("pricng")[0] is not None

    def test_the_bar_can_be_raised(self):
        strict = Corrections(similarity=0.99)
        assert strict._best("remte", frozenset({"remote"})) == "remte"

    def test_the_minimum_length_can_be_raised(self):
        longer = Corrections(minimum_length=10)
        assert longer._best("remte", frozenset({"remote"})) == "remte"

    def test_an_empty_vocabulary_changes_nothing(self):
        assert Corrections().apply(["remte"], frozenset()) == ["remte"]

    @pytest.mark.parametrize("similarity", [0.0, -0.1, 1.5])
    def test_a_nonsense_similarity_is_refused(self, similarity):
        with pytest.raises(TuningError, match="similarity"):
            Corrections(similarity=similarity)

    def test_a_zero_minimum_length_is_refused(self):
        with pytest.raises(TuningError, match="at least 1"):
            Corrections(minimum_length=0)

    def test_describe_says_when_it_is_off(self):
        assert "off" in Corrections(enabled=False).describe()

    def test_describe_names_the_settings_when_on(self):
        described = Corrections().describe()
        assert "0.8" in described
        assert "4 characters" in described


class TestCorrectionHappensBeforeExpansion:
    """A mistyped short form has to become the short form before the synonym
    map, which is keyed on the correct spelling, can recognize it."""

    def test_a_mistyped_short_form_still_expands(self):
        entries = [Entry(question="Are you open to remote work?", answer="Yes.")]
        index = Index(
            entries,
            tuning=Tuning().with_synonyms({"wfh": "remote work"}),
        )
        # "wfh" has to be in the vocabulary for a typo of it to correct, so
        # it is added through an alias.
        with_alias = Index(
            [Entry(question="Are you open to remote work?", answer="Yes.", aliases=["wfh"])],
            tuning=Tuning().with_synonyms({"wfh": "remote work"}),
        )
        assert with_alias.answer("wfhh")[0] is not None
        assert index.answer("remote work")[0] is not None
