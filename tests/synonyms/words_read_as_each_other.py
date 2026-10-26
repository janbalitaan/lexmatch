"""Fixtures the tests split out of words_read_as_each_other share.

The data for "words read as each other", kept in one place so that reducing each
test file to a single class did not mean copying it.
"""

from __future__ import annotations

from lexmatch import Entry

ENTRIES = [
    Entry(question="Are you open to remote work?", answer="Yes."),
    Entry(question="What is your compensation expectation?", answer="Negotiable."),
]
