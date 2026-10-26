"""A question set that could not be read."""

from __future__ import annotations

from lexmatch.exceptions.base import LexmatchError


class ParseError(LexmatchError):
    """A question set file is not shaped the way its format requires.

    Carries where the problem is — a line number, a row number, a key —
    because a question set is usually long and generated, and "something is
    wrong with your file" costs whoever owns it an afternoon.
    """
