"""Raised when a synonym map cannot work."""

from __future__ import annotations

from lexmatch.exceptions.base import LexmatchError


class SynonymError(LexmatchError, ValueError):
    """A synonym is declared in a way that could never match.

    A multi-word key is the common case: expansion happens one token at a
    time, so `{"work from home": "remote"}` would never fire. Raised rather
    than ignored, because a synonym map that silently does nothing looks
    exactly like one that is working — the queries it was meant to catch keep
    scoring zero and the cause is invisible.
    """
