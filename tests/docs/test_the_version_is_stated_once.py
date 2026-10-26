"""The version is written in two places, and they have to agree.

`pyproject.toml` carries it for the build and `__init__.py` carries it for
`lexmatch.__version__`. Nothing made them match, so a release could ship a
wheel labelled 0.2.0 whose module still said 0.1.0.

That matters more than it usually would: PyPI permanently reserves a filename
once uploaded — deleting the release does not free it — so a wrong version
cannot be corrected in place, only superseded.
"""

from __future__ import annotations

from importlib.metadata import version
from pathlib import Path
import re

import lexmatch

ROOT = Path(__file__).resolve().parents[2]


class TestTheVersionIsStatedOnce:
    @staticmethod
    def _declared() -> str:
        """The version in pyproject.toml, read without a TOML parser.

        tomllib arrived in 3.11 and this project supports 3.10, so the line
        is matched directly rather than adding a dependency for one field.
        """
        match = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.M)
        assert match, "pyproject.toml should declare a version"
        return match.group(1)

    def test_the_module_agrees_with_the_project(self):
        assert lexmatch.__version__ == self._declared()

    def test_the_installed_distribution_agrees_too(self):
        """Catches a stale editable install as well as a typo."""
        assert version("lexmatch") == self._declared()

    def test_the_changelog_has_an_entry_for_it(self):
        changelog = (ROOT / "CHANGELOG.md").read_text()
        assert f"## [{self._declared()}]" in changelog

    def test_the_changelog_entry_is_dated(self):
        changelog = (ROOT / "CHANGELOG.md").read_text()
        assert re.search(
            rf"^## \[{re.escape(self._declared())}\] — \d{{4}}-\d{{2}}-\d{{2}}$",
            changelog,
            re.M,
        ), "the released version needs a dated changelog heading"
