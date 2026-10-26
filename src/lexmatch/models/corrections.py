"""Reading a word somebody mistyped."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from difflib import SequenceMatcher

from lexmatch.constants import (
    CORRECTION_MINIMUM_LENGTH,
    CORRECTION_SIMILARITY,
)
from lexmatch.exceptions import TuningError


@dataclass(frozen=True)
class Corrections:
    """Maps a mistyped word onto the index's own vocabulary.

    A lexical matcher is unforgiving about spelling in a way that reads as
    stupidity: "whats your raets" scored 0.000 and was refused, while a
    person reading it would answer without noticing the typo. Nothing about
    aliases or synonyms helps, because the misspelling is not a word anybody
    would think to declare.

    So an unrecognized token is compared against the vocabulary the index
    actually contains, and replaced by the closest match when the match is
    close enough to be the same word mistyped.

    **Only unrecognized tokens.** A token already in the vocabulary is left
    exactly as it is — correction never overrides a real word, because the
    real word is the better evidence.

    Deliberately conservative, since a wrong correction answers a question
    nobody asked:

    * short tokens are skipped entirely. At three characters or fewer almost
      everything is within one edit of everything, so "api" would "correct"
      to "and";
    * the similarity bar is high, and measured on the whole token;
    * exactly one candidate has to be closest. A tie means the word is
      ambiguous and guessing picks wrong half the time.
    """

    similarity: float = CORRECTION_SIMILARITY
    minimum_length: int = CORRECTION_MINIMUM_LENGTH
    enabled: bool = True

    def __post_init__(self) -> None:
        """Reject a configuration that would correct recklessly."""
        if not 0.0 < self.similarity <= 1.0:
            raise TuningError(
                f"correction similarity has to be above 0 and at most 1 (got "
                f"{self.similarity}); at or below 0 every word matches every "
                "other and the index answers at random"
            )
        if self.minimum_length < 1:
            raise TuningError(
                f"correction minimum_length has to be at least 1 (got "
                f"{self.minimum_length}); an empty token has nothing to compare"
            )

    def apply(self, tokens: Iterable[str], vocabulary: frozenset[str]) -> list[str]:
        """Return the tokens with recognizable misspellings corrected."""
        if not self.enabled or not vocabulary:
            return list(tokens)
        return [self._best(token, vocabulary) for token in tokens]

    def _best(self, token: str, vocabulary: frozenset[str]) -> str:
        """Return the vocabulary word this token probably is, or the token.

        Compared only against words of a similar length. A token cannot be a
        typo of something three characters longer, and skipping those is both
        more accurate and much less work than ratio-ing the whole vocabulary.
        """
        if token in vocabulary or len(token) < self.minimum_length:
            return token
        spread = max(1, len(token) // 3)
        best: list[str] = []
        highest = self.similarity
        for candidate in vocabulary:
            if abs(len(candidate) - len(token)) > spread:
                continue
            ratio = SequenceMatcher(None, token, candidate).ratio()
            if ratio > highest:
                highest, best = ratio, [candidate]
            elif ratio == highest and candidate not in best:
                best.append(candidate)
        # One clear winner only. Two candidates equally close means the word
        # is ambiguous, and picking one is wrong half the time.
        return best[0] if len(best) == 1 else token

    def describe(self) -> str:
        """Summarize, for a line that is safe to log."""
        if not self.enabled:
            return "typo correction off"
        return (
            f"typo correction at {self.similarity} similarity, "
            f"{self.minimum_length} characters and up"
        )
