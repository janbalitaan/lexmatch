"""The limitations the README states, which are claims too."""

from __future__ import annotations

from importlib.metadata import requires

import pytest

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
        """README: 'No dependencies'. The packaged metadata has to agree.

        Read from the installed distribution rather than from pyproject.toml,
        because what a user gets is the metadata — and because tomllib is only
        in the standard library from 3.11 while this package supports 3.10.
        """
        assert not requires("lexmatch")
