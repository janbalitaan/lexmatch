"""Nothing public is undeclared."""

from __future__ import annotations

from itertools import groupby

import lexmatch
from tests.docs.the_public_surface import _ORDER, _is_module, _kind_of


class TestNothingPublicIsUndeclared:
    def test_every_public_module_attribute_is_in_all(self):
        """A name reachable but undeclared is one nobody knows is supported,
        and one that cannot be removed later without surprising somebody."""
        public = {
            name
            for name in vars(lexmatch)
            if not name.startswith("_") and not _is_module(getattr(lexmatch, name))
        }
        undeclared = sorted(public - set(lexmatch.__all__))
        assert undeclared == [], f"reachable but not in __all__: {undeclared}"

    def test_all_is_grouped_by_kind(self):
        """Constants, then classes, then functions — which is how secretref
        and maskvault read too, and more useful than alphabetical: a reader
        looking for "what can I configure" finds the constants together.

        Checked rather than asserted alphabetically, because an earlier
        version of this test demanded a strict sort and was simply imposing
        a convention the package had not chosen.
        """
        names = [n for n in lexmatch.__all__ if not n.startswith("_")]
        kinds = [_kind_of(name) for name in names]
        assert kinds == sorted(kinds, key=_ORDER.index), (
            f"__all__ mixes kinds: {list(zip(names, kinds, strict=True))}"
        )

    def test_each_group_is_sorted_within_itself(self):
        """So a new name has one obvious place to go."""
        names = [n for n in lexmatch.__all__ if not n.startswith("_")]
        for kind, group in groupby(names, key=_kind_of):
            members = list(group)
            assert members == sorted(members), f"the {kind} group is unsorted: {members}"

    def test_there_are_no_duplicates(self):
        assert len(lexmatch.__all__) == len(set(lexmatch.__all__))
