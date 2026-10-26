"""One question and the answer to it."""

from __future__ import annotations

from dataclasses import dataclass, field

from lexmatch.exceptions import EntryError
from lexmatch.text import normalize


@dataclass
class Entry:
    """One question/answer pair the owner wrote."""

    question: str
    answer: str
    aliases: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Refuse an entry that could never answer anything.

        Checked here rather than left to fail at match time, because the two
        are indistinguishable afterwards: an entry with a blank question
        scores zero against every query, exactly as an entry about something
        nobody asks does. One is a broken question set and the other is
        normal, and no amount of looking at scores separates them.

        A question of nothing but punctuation is refused for the same reason
        — "???" normalizes to no tokens at all, so the entry is unreachable
        however it is queried.

        Blank aliases are dropped rather than refused. An alias is optional
        by nature, a trailing empty column is what a spreadsheet export
        looks like, and dropping one costs nothing.
        """
        self.aliases = [alias for alias in self.aliases if alias.strip()]
        self.tags = [tag for tag in self.tags if tag.strip()]
        if not self.question.strip():
            raise EntryError(
                f"an entry needs a question; got {self.question!r} "
                f"(answer: {self.answer[:40]!r})"
            )
        if not self.answer.strip():
            raise EntryError(
                f"an entry needs an answer; got {self.answer!r} "
                f"(question: {self.question[:40]!r})"
            )
        if not normalize(self.question, keep_stopwords=True):
            raise EntryError(
                f"the question {self.question!r} leaves no tokens once "
                f"normalized, so no query could ever match this entry. Words "
                f"shorter than Tokenizer.SHORTEST_WORD are dropped, which is "
                f"what makes a one-letter question — 'C', 'R' — unmatchable"
            )

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
