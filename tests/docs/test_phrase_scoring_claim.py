"""TestPhraseScoringClaim."""

from __future__ import annotations

import pytest

from lexmatch import (
    DEFAULT_THRESHOLD,
    Entry,
    Index,
    normalize,
)


@pytest.fixture
def index() -> Index:
    """The exact index the README's opening example builds."""
    return Index(
        [
            Entry(
                "What do you do?",
                "I build backend services.",
                aliases=["what is your job", "what is your role"],
            ),
            Entry(
                "Are you open to remote work?",
                "Yes, and to relocation.",
                aliases=["remote", "relocate", "would you move", "hybrid"],
            ),
        ]
    )


class TestPhraseScoringClaim:
    def test_a_stopword_only_query_still_matches(self, index):
        """README: 'BM25 cannot rank "what do you do?" ... so phrasing is
        scored separately'."""
        entry, score = index.answer("what do you do")
        assert entry is not None
        assert score > DEFAULT_THRESHOLD

    def test_the_bare_dice_figure_the_readme_cites(self):
        """README cites 0.57 for 'what is 2+2' against 'what is your job'.

        That is the Dice coefficient over the shared tokens, which is what the
        substantive-overlap guard exists to discard.
        """
        query = set(normalize("what is 2+2", keep_stopwords=True))
        target = set(normalize("what is your job", keep_stopwords=True))
        shared = query & target
        dice = 2 * len(shared) / (len(query) + len(target))
        assert round(dice, 2) == 0.57

    def test_the_guard_discards_it(self):
        """README: the guard requires the substantive words to overlap too."""
        index = Index([Entry("What is your job?", "Backend.", aliases=["what is your job"])])
        entry, score = index.answer("what is 2+2")
        assert entry is None
        assert score == 0.0
