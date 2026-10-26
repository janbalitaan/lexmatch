"""The gap they close."""

from __future__ import annotations

import pytest

from lexmatch import Index
from tests.synonyms.words_read_as_each_other import ENTRIES


class TestWithoutSynonymsAShortFormMisses:
    """The gap they close."""

    @pytest.mark.parametrize("query", ["wfh", "comp"])
    def test_it_scores_nothing(self, query):
        _, score = Index(ENTRIES).answer(query)
        assert score == 0.0

    def test_no_threshold_reaches_it(self):
        """There is no signal to find, so lowering the threshold cannot help."""
        assert Index(ENTRIES, threshold=0.01).answer("wfh")[0] is None
