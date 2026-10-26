"""Everything a chatbot turn needs to say something sensible."""

from __future__ import annotations

from dataclasses import dataclass, field

from lexmatch.models.entry import Entry
from lexmatch.models.outcome import Outcome


@dataclass(frozen=True)
class Reply:
    """One answer, with why it is that answer and what else it might be.

    `answer()` returns a pair, which is enough for "did anything match". It
    is not enough to behave like a chatbot, because the three ways a query
    can fail to produce one answer need three different things said:

        nothing matched       "I don't know that. Try one of these."
        two matched equally   "Which did you mean — design or review?"
        a negative question   nothing confident; the match is the opposite

    Collapsing those into `(None, 0.0)` is how a bot ends up answering about
    design rates when it was asked about rates.
    """

    outcome: Outcome
    entry: Entry | None = None
    score: float = 0.0
    alternatives: tuple[Entry, ...] = field(default_factory=tuple)
    suggestions: tuple[str, ...] = field(default_factory=tuple)

    @property
    def answered(self) -> bool:
        """Whether there is an answer to give."""
        return self.outcome is Outcome.ANSWERED and self.entry is not None

    @property
    def text(self) -> str:
        """The answer, or an empty string when there is none.

        So a caller that only wants the happy path can write
        `reply.text or fallback()` without reaching into the entry.
        """
        return self.entry.answer if self.answered and self.entry else ""

    def describe(self) -> str:
        """Summarize this reply in one line, safe to log.

        Carries the outcome and the shape of the result but no question text
        and no answer text — a log of what visitors asked is personal data,
        and its retention should be a deliberate decision rather than a
        side effect of debugging.
        """
        parts = [self.outcome.value, f"score {self.score:.3f}"]
        if self.alternatives:
            parts.append(f"{len(self.alternatives)} alternatives")
        if self.suggestions:
            parts.append(f"{len(self.suggestions)} suggestions")
        return ", ".join(parts)
