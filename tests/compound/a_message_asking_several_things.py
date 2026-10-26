"""Fixtures the tests split out of a_message_asking_several_things share.

The data for "a message asking several things", kept in one place so that reducing each
test file to a single class did not mean copying it.
"""

from __future__ import annotations

from lexmatch import Entry

ENTRIES = [
    Entry(
        question="Are you open to remote work?",
        answer="Yes, six years of it.",
        aliases=["remote", "work from home", "wfh"],
    ),
    Entry(
        question="What are your rates?",
        answer="It depends on scope.",
        aliases=["pricing", "day rate", "how much"],
    ),
    Entry(
        question="What is your notice period?",
        answer="One month.",
        aliases=["when can you start", "availability"],
    ),
]
