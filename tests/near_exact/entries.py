"""Entries the near-exact wording tests share.

Several of them have questions whose words are nearly all stopwords, which
is the case containment exists for.
"""

from __future__ import annotations

from lexmatch import Entry

ENTRIES = [
    Entry("What are you working on right now?", "WORKING", ["current role"]),
    Entry("Are you open to remote work?", "REMOTE", ["remote", "wfh"]),
    Entry("Can you start work next month?", "START", ["availability"]),
    Entry("Do you enjoy the work?", "ENJOY", ["enjoyment"]),
    Entry("How do you approach testing?", "TESTING", ["testing", "qa"]),
]
