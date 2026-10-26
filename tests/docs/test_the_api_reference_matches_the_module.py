"""The api reference matches the module."""

from __future__ import annotations

import re

import lexmatch
from tests.docs.the_docs_are_true import DOCS


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
