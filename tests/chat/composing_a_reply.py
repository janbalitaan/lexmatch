"""Fixtures the tests split out of composing_a_reply share.

The data for "composing a reply", kept in one place so that reducing each
test file to a single class did not mean copying it.
"""

from __future__ import annotations

from lexmatch import Entry

ENTRIES = [
    Entry(
        question="What is your rate for design work?",
        answer="Design is £600 a day.",
        aliases=["design rate"],
    ),
    Entry(
        question="What is your rate for review work?",
        answer="Review is £500 a day.",
        aliases=["review rate"],
    ),
    Entry(
        question="What is your notice period?",
        answer="I need one month's notice.",
        aliases=["availability"],
    ),
    Entry(
        question="Are you open to remote work?",
        answer="Yes, I have worked remotely for six years",
        aliases=["remote"],
    ),
]
