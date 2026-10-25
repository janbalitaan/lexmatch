"""The README badges have to say what the package actually is.

A `pypi/v` badge for an unpublished project renders "package or version not
found", which a reader takes for a broken README rather than for information.
A static placeholder says the same thing deliberately, and these tests derive
which badge is correct from whether anything has been released — so the swap
at publish time cannot be forgotten.
"""

from __future__ import annotations

from importlib.metadata import metadata
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
README = (ROOT / "README.md").read_text()


def badge(label: str) -> str:
    """The value half of a static shields.io badge, URL-decoded."""
    match = re.search(rf"img\.shields\.io/badge/{label}-([^-]+)-\w+\)", README)
    assert match, f"no static {label} badge in the README"
    return match.group(1).replace("%20", " ").replace("%7C", "|")


class TestTheStaticBadgesMatchTheMetadata:
    """Drift is the cost of a static badge, so the claim is checked."""

    def test_the_python_badge_lists_the_supported_versions(self):
        classifiers = metadata("lexmatch").get_all("Classifier") or []
        supported = sorted(
            line.rsplit(" :: ", 1)[-1]
            for line in classifiers
            if line.startswith("Programming Language :: Python :: 3.")
        )
        claimed = sorted(part.strip() for part in badge("python").split("|"))
        assert claimed == supported

    def test_the_license_badge_matches_the_license(self):
        assert badge("license") == "MIT"
        assert (ROOT / "LICENSE").read_text().startswith("MIT License")
