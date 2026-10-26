"""Fixtures the tests split out of scoring_is_tunable share.

The data for "scoring is tunable", kept in one place so that reducing each
test file to a single class did not mean copying it.
"""

from __future__ import annotations

from lexmatch import Entry

ENTRIES = [
    Entry(question="Are you open to remote work?", answer="Yes.", aliases=["remote"]),
    Entry(question="Can you start next month?", answer="Yes.", aliases=["availability"]),
]

DILUTED = [
    Entry(question="What is your rate for design work?", answer="A.", aliases=[]),
    Entry(question="What is your rate for review work?", answer="B.", aliases=[]),
    Entry(question="What is your rate for audit work?", answer="C.", aliases=[]),
    Entry(question="What is your rate for training work?", answer="D.", aliases=[]),
]
