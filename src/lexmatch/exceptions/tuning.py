"""Raised when scoring is configured in a way that cannot work."""

from __future__ import annotations

from lexmatch.exceptions.base import LexmatchError


class TuningError(LexmatchError, ValueError):
    """A tuning value is outside the range it has to be in.

    Raised at construction rather than at scoring time. A threshold above 1
    answers nothing and a saturation of 0 divides by zero, and both would
    otherwise surface as an index that silently never matches — which reads
    as "my questions are worded badly" rather than as a configuration error.

    Also a `ValueError`, because that is what a caller validating input will
    already be catching.
    """
