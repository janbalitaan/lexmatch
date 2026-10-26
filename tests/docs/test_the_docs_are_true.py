"""The documentation is checked, not trusted.

Writing these pages produced two invented numbers — a score of 0.812 that was
really 0.667, and figures quoted as fixed when IDF makes them drift with the
size of the index. Both were caught by running the examples rather than by
rereading the prose, which is what this file does from now on.
"""

from __future__ import annotations

from pathlib import Path
import re

import pytest

import lexmatch
from lexmatch import Entry, Index, Tuning

DOCS = Path(__file__).resolve().parents[2] / "docs"
PAGES = sorted(DOCS.glob("*.md"))


class TestThePagesExist:
    def test_there_are_pages(self):
        assert PAGES, "no documentation found"

    def test_the_index_lists_every_page(self):
        """A page nobody links to is a page nobody reads."""
        listed = (DOCS / "README.md").read_text()
        for page in PAGES:
            if page.name == "README.md":
                continue
            assert page.name in listed, f"{page.name} is not linked from docs/README.md"

    @pytest.mark.parametrize("page", PAGES, ids=lambda item: item.name)
    def test_every_internal_link_resolves(self, page):
        for target in re.findall(r"\]\((?!https?://|#)([^)#]+)", page.read_text()):
            assert (DOCS / target).is_file(), f"{page.name} links to a missing {target}"

    @pytest.mark.parametrize("page", PAGES, ids=lambda item: item.name)
    def test_a_page_says_something(self, page):
        assert len(page.read_text().split()) > 60, f"{page.name} is a stub"


class TestTheApiReferenceMatchesTheModule:
    @staticmethod
    def _documented() -> set[str]:
        block = re.search(
            r"from lexmatch import \((.*?)\)", (DOCS / "api.md").read_text(), re.S
        )
        assert block, "api.md should open with an import block"
        return {name.strip().rstrip(",") for name in re.findall(r"[\w_]+,", block.group(1))}

    def test_every_public_name_is_documented(self):
        for name in lexmatch.__all__:
            assert name in self._documented(), f"{name} is public but not in api.md"

    def test_every_documented_name_is_importable(self):
        for name in self._documented():
            assert hasattr(lexmatch, name), f"api.md documents a missing {name}"


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
            "do you like working alone": (0.000, False),
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
            "work from home": (0.477, 1.000),
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
        assert abs(loose.score(query)[0][0] - 0.769) < 0.001
        assert abs(strict.score(query)[0][0] - 0.042) < 0.001
        assert loose.answer(query)[0] is not None
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
