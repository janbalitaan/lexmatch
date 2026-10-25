"""Turning a string into comparable tokens."""

from __future__ import annotations

import re
from typing import ClassVar
import unicodedata

from lexmatch.stopwords import STOPWORDS


class Tokenizer:
    """Splits text into the tokens scoring compares.

    Class methods rather than instance ones: tokenizing is a calculation with
    no state, and requiring a caller to construct something before reaching a
    pure function buys nothing. The class groups them under one name, so "how
    is text split" has a single place to look — and gives the word pattern
    somewhere to live that is not module scope.
    """

    # What counts as a word. Dots and the hash survive so "node.js" and "C#"
    # stay whole, because a technology name split in two matches nothing.
    # A class attribute rather than a module constant: it is this class's
    # working detail, and nothing else should reach for it.
    _WORD: ClassVar[re.Pattern[str]] = re.compile(r"[a-z0-9+#.]+")

    @classmethod
    def normalize(cls, text: str, keep_stopwords: bool = False) -> list[str]:
        """Lowercase, strip accents, split into comparable terms.

        Accent folding matters because a visitor may type "resume" for "résumé".
        """
        text = unicodedata.normalize("NFKD", text.lower())
        text = "".join(char for char in text if not unicodedata.combining(char))
        words = [word for word in cls._WORD.findall(text) if len(word) > 1]
        if keep_stopwords:
            return words
        return [word for word in words if word not in STOPWORDS]

    @classmethod
    def query_terms(cls, text: str) -> list[str]:
        """Terms for a search, never empty for non-empty input.

        "What do you do?" is every bit a real question, and every word in it is a
        stopword. Stripping them leaves nothing to match, so for queries that come
        back empty we keep the stopwords — the index holds them too.
        """
        terms = cls.normalize(text)
        return terms or cls.normalize(text, keep_stopwords=True)
