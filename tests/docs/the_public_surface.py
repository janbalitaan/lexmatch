"""Fixtures the tests split out of the_public_surface share.

The data for "the public surface", kept in one place so that reducing each
test file to a single class did not mean copying it.
"""

from __future__ import annotations

import types

import lexmatch

_ORDER = ("constant", "class", "function")


def _kind_of(name: str) -> str:
    """Classify a public name the way `__all__` groups them."""
    value = getattr(lexmatch, name)
    if name.isupper():
        return "constant"
    if isinstance(value, type):
        return "class"
    return "function"


def _is_module(value: object) -> bool:
    """Whether this attribute is a submodule rather than part of the API."""
    return isinstance(value, types.ModuleType)
