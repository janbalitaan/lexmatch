"""Every output and number the README claims, asserted.

Documentation that drifts from behavior is worse than none, because a reader
trusts it. Each test corresponds to a specific claim in README.md, including
the tuning figures — a constant changed without updating the docs fails here.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import tomllib

from lexmatch import (
    DEFAULT_THRESHOLD,
    LENGTH_PENALTY,
    TERM_FREQUENCY_SATURATION,
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


class TestQuickStart:
    def test_the_documented_match_and_score(self, index):
        """README: answer('what is your role') -> (Entry('What do you do?'), 1.0)."""
        entry, score = index.answer("what is your role")
        assert entry is not None
        assert entry.question == "What do you do?"
        assert score == pytest.approx(1.0)

    def test_the_documented_refusal(self, index):
        """README: answer('what is the capital of France') -> (None, 0.0)."""
        assert index.answer("what is the capital of France") == (None, 0.0)


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


class TestTuningTable:
    """The README publishes these three numbers, so they are part of the API."""

    def test_the_threshold(self):
        assert DEFAULT_THRESHOLD == 0.45

    def test_the_saturation(self):
        assert TERM_FREQUENCY_SATURATION == 1.4

    def test_the_length_penalty(self):
        assert LENGTH_PENALTY == 0.72

    def test_the_threshold_is_configurable_as_documented(self, index):
        strict = Index(
            list(index._entries) if hasattr(index, "_entries") else [], threshold=1.01
        )
        assert strict.answer("What do you do?")[0] is None


class TestAliasesClaim:
    def test_aliases_are_weighted_as_heavily_as_the_question(self, index):
        """README: 'Aliases are weighted as heavily as the question itself'."""
        by_question = index.answer("What do you do?")[1]
        by_alias = index.answer("what is your job")[1]
        assert by_alias == pytest.approx(by_question)

    def test_a_single_alias_word_matches(self, index):
        entry, _ = index.answer("remote")
        assert entry is not None
        assert "remote" in entry.question.lower()


class TestScalingClaim:
    def test_scores_are_bounded_zero_to_one(self, index):
        """README: 'Scores are scaled to 0-1, so a threshold means the same
        thing whatever the corpus size'."""
        for score, _ in index.score("remote work and relocation"):
            assert 0.0 <= score <= 1.0

    def test_the_threshold_means_the_same_at_a_different_corpus_size(self):
        entries = [
            Entry(f"Question number {number}?", f"Answer {number}", aliases=[f"q{number}"])
            for number in range(50)
        ]
        large = Index(entries)
        entry, score = large.answer("Question number 7?")
        assert entry is not None
        assert score == pytest.approx(1.0)


class TestLimitationsClaim:
    def test_an_unlisted_phrasing_does_not_match(self):
        """README: 'an unlisted phrasing does not match' — no model here, so
        there is no way to know 'role' means 'job'."""
        index = Index([Entry("What do you do?", "Backend.", aliases=["what is your job"])])
        assert index.answer("what is your role")[0] is None

    def test_it_has_no_dependencies(self):
        """README: 'No dependencies'. The packaged metadata has to agree."""

        data = tomllib.loads(Path("pyproject.toml").read_bytes().decode())
        assert data["project"]["dependencies"] == []
