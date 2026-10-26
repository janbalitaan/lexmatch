"""Describe."""

from __future__ import annotations

from lexmatch.models.tuning import Tuning


class TestDescribe:
    def test_it_names_every_number(self):
        described = Tuning().describe()
        for part in ("threshold", "saturation", "length penalty", "minimum overlap"):
            assert part in described

    def test_it_counts_the_stopwords(self):
        described = Tuning().with_stopwords(["a", "b"]).describe()
        assert "2 stopwords" in described

    def test_it_does_not_list_them(self):
        """Safe to log: seventy-seven words in a log line is noise."""
        assert "what" not in Tuning().describe()
