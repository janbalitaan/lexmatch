"""Fixtures the tests split out of small_talk share.

The data for "small talk", kept in one place so that reducing each
test file to a single class did not mean copying it.
"""

from __future__ import annotations

from lexmatch import Entry

REPLIES = {
    "greeting": "Hello. Ask me anything about Jan's work.",
    "thanks": "You're welcome.",
    "farewell": "Take care.",
    "identity": "I'm a small bot that answers questions about Jan.",
    "capability": "Try asking about remote work or rates.",
    "wellbeing": "Well, thanks.",
}

CONTENT = [
    Entry(question="Are you open to remote work?", answer="Yes.", aliases=["remote"]),
    Entry(question="What are your rates?", answer="It depends.", aliases=["pricing"]),
]
