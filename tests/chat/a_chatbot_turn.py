"""Fixtures the tests split out of a_chatbot_turn share.

The data for "a chatbot turn", kept in one place so that reducing each
test file to a single class did not mean copying it.
"""

from __future__ import annotations

from lexmatch import Entry

ENTRIES = [
    Entry(
        question="What is your rate for design work?",
        answer="£600/day for design.",
        aliases=["design rate"],
    ),
    Entry(
        question="What is your rate for review work?",
        answer="£500/day for review.",
        aliases=["review rate"],
    ),
    Entry(question="Are you open to remote work?", answer="Yes.", aliases=["remote"]),
    Entry(
        question="What is your notice period?", answer="One month.", aliases=["availability"]
    ),
]

FIRST = Entry(question="What is your rate for design work?", answer="£600.")

SECOND = Entry(question="What is your rate for review work?", answer="£500.")

THIRD = Entry(question="What is your rate for audit work?", answer="£550.")

FOURTH = Entry(question="What is your notice period?", answer="One month.")
