"""Text normalization and tokenization for lexical matching."""

from __future__ import annotations

import re
import unicodedata

from lexmatch.stopwords import STOPWORDS

_WORD = re.compile(r"[a-z0-9+#.]+")


# A question is only answered when it clears this score. Tuned against the
# template corpus: off-topic questions score 0.2-0.4 from shared filler
# words alone, so the bar sits above that. Refusing is the right default —
# a confident wrong answer about someone's career is worse than no answer.


def normalize(text: str, keep_stopwords: bool = False) -> list[str]:
    """Lowercase, strip accents, split into comparable terms.

    Accent folding matters because a visitor may type "resume" for "résumé".
    """
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    words = [word for word in _WORD.findall(text) if len(word) > 1]
    if keep_stopwords:
        return words
    return [word for word in words if word not in STOPWORDS]


def query_terms(text: str) -> list[str]:
    """Terms for a search, never empty for non-empty input.

    "What do you do?" is every bit a real question, and every word in it is a
    stopword. Stripping them leaves nothing to match, so for queries that come
    back empty we keep the stopwords — the index holds them too.
    """
    terms = normalize(text)
    return terms or normalize(text, keep_stopwords=True)
