"""Fixtures the tests split out of small_talk_stays_in_its_lane share.

The data for "small talk stays in its lane", kept in one place so that reducing each
test file to a single class did not mean copying it.
"""

from __future__ import annotations

REPLIES = {
    "greeting": "Hello.",
    "farewell": "Take care.",
    "thanks": "You're welcome.",
    "identity": "I'm a bot.",
    "capability": "Ask about rates or availability.",
    "wellbeing": "Well, thanks.",
}
