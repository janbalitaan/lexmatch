"""The pages exist."""

from __future__ import annotations

import re

import pytest

from tests.docs.the_docs_are_true import DOCS, PAGES


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
