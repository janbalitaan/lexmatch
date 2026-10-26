"""Describe."""

from __future__ import annotations

from lexmatch import Synonyms, Tuning


class TestDescribe:
    def test_it_counts_them(self):
        assert "2 synonyms" in Synonyms.of({"a": "b", "c": "d"}).describe()

    def test_it_appears_in_the_tuning_summary(self):
        described = Tuning().with_synonyms({"wfh": "remote"}).describe()
        assert "1 synonyms" in described

    def test_it_does_not_list_them(self):
        """Safe to log."""
        assert "wfh" not in Synonyms.of({"wfh": "remote"}).describe()
