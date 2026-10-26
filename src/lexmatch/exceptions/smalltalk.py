"""Raised when small talk is configured for an intent that does not exist."""

from __future__ import annotations

from lexmatch.exceptions.base import LexmatchError


class SmallTalkError(LexmatchError, KeyError):
    """A small-talk intent this library does not know.

    Raised rather than ignored. A typo in an intent name leaves that handler
    silently absent, which looks exactly like one that is working right up
    until a visitor says hello and gets a refusal.

    Also a `KeyError`, since naming an intent is a lookup and that is what a
    caller validating one will already be catching.
    """
