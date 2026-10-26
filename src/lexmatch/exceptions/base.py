"""The base every lexmatch error derives from."""

from __future__ import annotations


class LexmatchError(Exception):
    """Something this library was asked to do that it cannot.

    One base so an application can catch everything from here with a single
    `except`, whichever part of the library raised it.
    """
