"""An entry that cannot answer anything."""

from __future__ import annotations

from lexmatch.exceptions.base import LexmatchError


class EntryError(LexmatchError):
    """An entry is missing the question or the answer it needs.

    Raised when the entry is built rather than when a query fails to match
    it, because the two are indistinguishable afterwards: an entry with a
    blank question scores zero against everything, exactly as an entry on a
    subject nobody asks about does. One is a bug in the question set and the
    other is normal, and nothing downstream can tell them apart.

    Question sets are generated as often as they are written — from a
    spreadsheet export, a content system, a CV parser — and a blank row is
    the ordinary failure of all three.
    """
