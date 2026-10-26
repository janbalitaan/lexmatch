"""Fixtures the tests split out of typos_are_read share.

The data for "typos are read", kept in one place so that reducing each
test file to a single class did not mean copying it.
"""

from __future__ import annotations

from lexmatch import Entry

ENTRIES = [
    Entry(question="Are you open to remote work?", answer="Yes.", aliases=["remote"]),
    Entry(question="What are your rates?", answer="It depends.", aliases=["pricing"]),
    Entry(
        question="What is your notice period?", answer="One month.", aliases=["availability"]
    ),
]

VOCABULARY = frozenset(
    {"remote", "work", "rates", "notice", "period", "python", "senior", "junior", "rust"}
)
