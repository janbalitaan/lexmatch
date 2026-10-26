"""A mistyped short form has to become the short form before the synonym
map, which is keyed on the correct spelling, can recognize it."""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index, Tuning
from tests.chat.typos_are_read import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


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
