"""With synonyms it matches."""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index, Tuning
from tests.synonyms.words_read_as_each_other import ENTRIES


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
