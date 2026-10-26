"""Fixtures the tests split out of json_is_read share.

The data for "json is read", kept in one place so that reducing each
test file to a single class did not mean copying it.
"""

from __future__ import annotations

ROWS = [
    {
        "question": "How do I reset my password?",
        "answer": "Use the Forgot password link.",
        "aliases": ["forgot password", "locked out"],
        "tags": ["account"],
    },
    {"question": "What is your refund policy?", "answer": "Full refund within 14 days."},
]
