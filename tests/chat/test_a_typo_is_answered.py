"""A typo is answered."""

from __future__ import annotations

import pytest

from lexmatch import Index, Tuning
from tests.chat.typos_are_read import ENTRIES


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
