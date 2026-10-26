"""Containment is only evidence when the query covers most of the phrasing.

Every short query is inside *something*: "you work" sits in "Do you enjoy
the work?", "Are you open to remote work?" and "Can you start work next
month?" alike, covering two tokens of five. Treating that as near-exact
wording put a three-way tie over the ambiguity floor and asked which was
meant.
"""

from __future__ import annotations

import pytest

from lexmatch import Index, Outcome, Tuning
from lexmatch.index import _NEAR_EXACT
from tests.near_exact.entries import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestContainmentNeedsCoverage:
    def test_a_thinly_contained_query_is_not_lifted(self, index):
        """0.571 coverage, under the bar, so the weighted comparison decides
        and the result is the refusal it was before."""
        forced = Index(ENTRIES, tuning=Tuning(ambiguity_margin=0.2))
        assert forced.reply("you work").outcome is not Outcome.ANSWERED

    def test_it_scores_below_the_threshold(self, index):
        assert index.score("you work")[0][0] < index.threshold

    def test_a_single_common_word_is_not_lifted(self, index):
        assert index.score("work")[0][0] < index.threshold

    def test_the_bar_is_stated(self):
        """So a change to it is deliberate."""
        assert _NEAR_EXACT == 0.70
