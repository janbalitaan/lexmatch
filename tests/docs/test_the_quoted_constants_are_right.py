"""A default written into prose drifts when the code changes."""

from __future__ import annotations

import re

import pytest

import lexmatch
from tests.docs.the_docs_are_true import DOCS


class TestTheQuotedConstantsAreRight:
    """A default written into prose drifts when the code changes."""

    @pytest.mark.parametrize(
        ("value", "name"),
        [
            ("0.45", "DEFAULT_THRESHOLD"),
            ("1.4", "TERM_FREQUENCY_SATURATION"),
            ("0.72", "LENGTH_PENALTY"),
        ],
    )
    def test_the_tuning_table_quotes_the_real_default(self, value, name):
        assert str(getattr(lexmatch, name)) == value, (
            f"docs quote {name} as {value}; it is {getattr(lexmatch, name)}"
        )
        assert value in (DOCS / "tuning.md").read_text()

    def test_the_stopword_count_is_right(self):
        count = len(lexmatch.STOPWORDS)
        for page in ("tuning.md", "scoring.md", "limitations.md"):
            text = (DOCS / page).read_text()
            if "stopword" in text and re.search(r"\b\d+ (shipped )?stopwords?\b", text):
                assert str(count) in text, f"{page} quotes a stale stopword count"
