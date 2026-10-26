"""Every error this library raises."""

from __future__ import annotations

from lexmatch.exceptions.base import LexmatchError
from lexmatch.exceptions.smalltalk import SmallTalkError
from lexmatch.exceptions.synonyms import SynonymError
from lexmatch.exceptions.tuning import TuningError

__all__ = ["LexmatchError", "SmallTalkError", "SynonymError", "TuningError"]
