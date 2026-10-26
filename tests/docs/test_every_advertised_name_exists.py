"""Every advertised name exists."""

from __future__ import annotations

import pytest

import lexmatch


class TestEveryAdvertisedNameExists:
    @pytest.mark.parametrize("name", lexmatch.__all__)
    def test_it_is_bound_on_the_module(self, name):
        assert hasattr(lexmatch, name), f"__all__ lists {name}, which is not importable"

    def test_a_star_import_works(self):
        """The thing `__all__` is actually for."""
        namespace: dict = {}
        exec("from lexmatch import *", namespace)
        for name in lexmatch.__all__:
            assert name in namespace
