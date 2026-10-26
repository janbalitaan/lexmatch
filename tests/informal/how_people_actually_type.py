"""Fixtures the tests split out of how_people_actually_type share.

The data for "how people actually type", kept in one place so that reducing each
test file to a single class did not mean copying it.
"""

from __future__ import annotations

from lexmatch import Entry

ENTRIES = [
    Entry(
        question="What is your notice period?",
        answer="NOTICE",
        aliases=["notice", "when can you start", "availability"],
    ),
    Entry(
        question="Are you open to remote work?",
        answer="REMOTE",
        aliases=["remote", "work from home"],
    ),
    Entry(
        question="What are your rate expectations?", answer="RATE", aliases=["rate", "salary"]
    ),
    Entry(
        question="Have you led a team?",
        answer="LEADERSHIP",
        aliases=["leadership", "led teams", "managed a team"],
    ),
    Entry(question="How do you reduce cost?", answer="COST", aliases=["cost", "cloud spend"]),
    Entry(
        question="How many years of experience?",
        answer="YEARS",
        aliases=["experience", "years"],
    ),
]
