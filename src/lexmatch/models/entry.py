"""One question and the answer to it."""

from __future__ import annotations

from dataclasses import dataclass, field

from lexmatch.text import normalize


@dataclass
class Entry:
    """One question/answer pair the owner wrote."""

    question: str
    answer: str
    aliases: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def asked_phrases(self) -> list[str]:
        """Return the question and its aliases, normalized, for phrase matching."""
        return [
            " ".join(normalize(phrasing, keep_stopwords=True))
            for phrasing in [self.question, *self.aliases]
            if phrasing.strip()
        ]

    def terms(self) -> list[str]:
        """Every term that should match this entry.

        The question and aliases are repeated so that matching on how a
        visitor *asked* outranks a word buried in a long answer. Stopwords are
        kept for them, so queries made entirely of stopwords still match.
        """
        asked = " ".join([self.question] * 3 + self.aliases * 3 + self.tags * 2)
        return normalize(asked, keep_stopwords=True) + normalize(self.answer)
