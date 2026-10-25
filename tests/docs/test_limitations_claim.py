"""TestLimitationsClaim."""

from __future__ import annotations

from pathlib import Path

import pytest
import tomllib

from lexmatch import (
    Entry,
    Index,
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
