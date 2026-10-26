"""A replaced weight table that returns zero must not divide by it.

Phrase overlap is weighted by inverse document frequency, so a shared
question form does not look like a shared subject. The built-in weights
are never zero — the `+ 1` guard leaves a term that appears in every
entry at about 0.29 — so the fallback cannot be reached through the
public surface.

It exists because the weights are a plain mapping, and the library's
stated position is that a developer may replace one. These tests reach in
to do exactly that, because the alternative is an untested branch that
turns a customization into a `ZeroDivisionError`."""

from __future__ import annotations

from typing import ClassVar

import pytest

from lexmatch import Entry, Index


@pytest.fixture
def entries() -> list[Entry]:
    return [
        Entry(
            "What do you do?",
            "I build backend services.",
            aliases=["what is your job", "what is your role"],
            tags=["opening"],
        ),
        Entry(
            "Are you open to remote work?",
            "Yes, and to relocation.",
            aliases=["remote", "relocate", "would you move"],
            tags=["logistics"],
        ),
        Entry(
            "Tell me about a time you made a mistake",
            "I shipped a migration with no rollback.",
            aliases=["a failure", "something you got wrong"],
            tags=["experience"],
        ),
        Entry(
            "What are your salary expectations?",
            "Let us discuss that in context.",
            aliases=["salary", "compensation", "rate"],
            tags=["boundary"],
        ),
    ]


@pytest.fixture
def index(entries) -> Index:
    return Index(entries)


class TestTheWeightedOverlapFallsBackOnZeroWeight:
    """A replaced weight table that returns zero must not divide by it.

    Phrase overlap is weighted by inverse document frequency, so a shared
    question form does not look like a shared subject. The built-in weights
    are never zero — the `+ 1` guard leaves a term that appears in every
    entry at about 0.29 — so the fallback cannot be reached through the
    public surface.

    It exists because the weights are a plain mapping, and the library's
    stated position is that a developer may replace one. These tests reach in
    to do exactly that, because the alternative is an untested branch that
    turns a customization into a `ZeroDivisionError`.
    """

    ENTRIES: ClassVar[list[Entry]] = [
        Entry(question="are you open to remote work", answer="Yes.", aliases=[]),
    ]

    def test_the_built_in_weights_are_never_zero(self):
        """The premise: this is why the branch needs reaching into."""
        index = Index(self.ENTRIES)
        assert all(value > 0 for value in index._inverse_document_frequency.values())

    def test_a_zeroed_weight_table_counts_tokens_instead(self):
        index = Index(self.ENTRIES)
        index._inverse_document_frequency = dict.fromkeys(
            index._inverse_document_frequency, 0.0
        )
        shared = {"remote", "work"}
        # The masses are passed in now, built with the index. Zero for both
        # is what a replaced weight table produces, which is the case here.
        score = index._weighted_dice(
            shared, shared | {"pay"}, frozenset(shared | {"open"}), 0.0, 0.0
        )
        assert score == 2 * 2 / (3 + 3)

    def test_a_zeroed_table_does_not_raise_through_score(self):
        index = Index(self.ENTRIES)
        index._inverse_document_frequency = dict.fromkeys(
            index._inverse_document_frequency, 0.0
        )
        assert index.score("are you open to remote work")[0][0] >= 0
