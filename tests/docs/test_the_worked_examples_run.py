"""Every score quoted in a page, recomputed."""

from __future__ import annotations

import pytest

from lexmatch import Entry, Index, Tuning
from tests.docs.the_docs_are_true import DOCS


class TestTheWorkedExamplesRun:
    """Every score quoted in a page, recomputed."""

    @pytest.fixture
    def remote_and_notice(self) -> Index:
        return Index(
            [
                Entry(
                    question="Are you open to remote work?",
                    answer="Yes.",
                    aliases=["remote", "work from home", "distributed team"],
                ),
                Entry(
                    question="What is your notice period?",
                    answer="One month.",
                    aliases=["when can you start", "availability", "how soon"],
                ),
            ]
        )

    def test_refusing_quotes_real_scores(self, remote_and_notice):
        """The table in refusing.md, line by line."""
        expected = {
            "remote": (1.000, True),
            "how soon can you start": (0.952, True),
            "what is the capital of france": (0.000, False),
            "do you enjoy cooking": (0.000, False),
            "what is the weather": (0.000, False),
            "": (0.000, False),
        }
        for query, (score, answered) in expected.items():
            entry, actual = remote_and_notice.answer(query)
            assert (entry is not None) is answered, f"{query!r} answered unexpectedly"
            assert abs(actual - score) < 0.001, f"{query!r}: doc {score}, actual {actual:.3f}"

    def test_aliases_quotes_real_scores(self):
        """The before-and-after table in aliases.md."""
        without = Index([Entry(question="Are you open to remote work?", answer="Yes.")])
        with_them = Index(
            [
                Entry(
                    question="Are you open to remote work?",
                    answer="Yes.",
                    aliases=["work from home", "distributed team", "wfh"],
                )
            ]
        )
        expected = {
            "work from home": (0.955, 1.000),
            "wfh": (0.000, 1.000),
            "distributed team": (0.000, 1.000),
        }
        for query, (bare, aliased) in expected.items():
            assert abs(without.answer(query)[1] - bare) < 0.001, query
            assert abs(with_them.answer(query)[1] - aliased) < 0.001, query

    def test_tuning_quotes_real_overlap_scores(self):
        """The minimum_overlap table in tuning.md."""
        entries = [
            Entry(question=f"What is your rate for {word} work?", answer="A.")
            for word in ("design", "review", "audit", "training")
        ]
        query = "what is your rate for consulting"
        loose = Index(entries, tuning=Tuning(minimum_overlap=1))
        strict = Index(entries, tuning=Tuning(minimum_overlap=2))
        assert abs(loose.score(query)[0][0] - 0.139) < 0.001
        assert abs(strict.score(query)[0][0] - 0.084) < 0.001
        # Both are refused at the default threshold, which the doc now says
        # outright. It used to claim the loose one was answered, which was
        # true only while phrase overlap counted tokens equally.
        assert loose.answer(query)[0] is None
        assert strict.answer(query)[0] is None

    def test_describe_matches_the_quoted_line(self):
        described = Tuning().describe()
        quoted = (DOCS / "tuning.md").read_text()
        for part in described.split(", "):
            assert part in quoted, f"tuning.md does not quote {part!r}"

    def test_getting_started_round_trips(self, remote_and_notice):
        entry, _ = remote_and_notice.answer("how soon could you start?")
        assert entry is not None
        assert entry.answer == "One month."

    def test_suggestions_returns_fewer_than_the_limit_on_a_small_index(self, remote_and_notice):
        """getting-started.md says so explicitly."""
        assert len(remote_and_notice.suggestions(limit=3)) == 2
