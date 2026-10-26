"""Turning a string into comparable tokens."""

from __future__ import annotations

import re
from typing import ClassVar
import unicodedata

from lexmatch.contractions import Contractions
from lexmatch.stopwords import STOPWORDS

#: A token needs a letter or a digit in it. The word pattern admits dots,
#: plus signs and hashes so "node.js", "c++" and "c#" survive whole, which
#: also made a run of them a token in its own right: "..." and "+++" were
#: indexed as words, and an entry whose question was "..." passed validation
#: as answerable.
_HAS_CONTENT = re.compile(r"[a-z0-9]")

#: Every apostrophe a keyboard or a word processor produces, mapped away.
#: The curly ones arrive from anything that autocorrects, which is most
#: phones.
_APOSTROPHES = str.maketrans(dict.fromkeys("'\u2019\u02bc\u055a\uff07", ""))


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

    #: The shortest token kept. Two, because a single character is almost
    #: always noise — an initial, a list marker, a stray letter from a split
    #: contraction — and "a" and "i" are stopwords anyway.
    #:
    #: The cost is that a one-letter technology name cannot be indexed: "C"
    #: and "R" are unmatchable, and an entry whose question is only one of
    #: them is refused when it is built, which is the honest outcome rather
    #: than a silent miss. Lowering this to 1 was measured and cost one
    #: question in 133 while gaining nothing the benchmarks could see, so it
    #: is not the default — but for an index that genuinely needs those
    #: names:
    #:
    #:     Tokenizer.SHORTEST_WORD = 1
    SHORTEST_WORD: ClassVar[int] = 2

    @classmethod
    def normalize(cls, text: str, keep_stopwords: bool = False) -> list[str]:
        """Lowercase, strip accents, split into comparable terms.

        Accent folding matters because a visitor may type "resume" for "résumé".
        """
        text = unicodedata.normalize("NFKD", text.lower())
        text = "".join(char for char in text if not unicodedata.combining(char))
        # Apostrophes go before splitting, not after. The word pattern does
        # not include one, so it *split* on it: "don't" became "don" and a
        # dropped "t", "you've" became "you" and "ve", and "what's" became
        # "what". The apostrophe form is the one people actually type, and it
        # was being handled worse than the stripped one — removing it first
        # turns both into "dont", which the contraction table expands.
        #
        # A possessive collapses the same way: "company's rate" becomes
        # "companys rate", and stemming folds that onto "company".
        text = text.translate(_APOSTROPHES)
        # A trailing period is sentence punctuation, not part of the word.
        # The pattern has to admit periods for "node.js", ".net" and "3.11",
        # which meant the last word of every sentence became its own term:
        # "context." was a token no query could ever match, so the final
        # word of each sentence in an answer was silently unsearchable.
        # Only the edges are trimmed, so "node.js" survives intact.
        words = [
            stripped
            for word in cls._WORD.findall(text)
            if (stripped := word.strip("."))
            and len(stripped) >= cls.SHORTEST_WORD
            and _HAS_CONTENT.search(stripped)
        ]
        # The apostrophe is gone by now, so "don't" is "dont" — a token in no
        # stopword list and in no entry, which the weighting would treat as
        # one of the most discriminating words there is. Expanded into the
        # words it stands for, which are ordinary stopwords.
        words = Contractions.expand(words)
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
