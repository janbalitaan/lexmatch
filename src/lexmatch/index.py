"""Deterministic answering — no model, no network, no API key.

This is the mode that keeps a bot answering after an AI quota is spent, and
the only mode some owners will ever turn on. It scores the visitor's question
against the question/answer pairs in answers.md and returns the owner's own
wording verbatim, or refuses.

BM25 rather than embeddings: embeddings need a model to build and a vector
store to query, which reintroduces the dependency this mode exists to remove.
A corpus of a few dozen answers is small enough that lexical scoring is both
accurate and instant, and the owner can predict what it will match.
"""

from __future__ import annotations

import math

from lexmatch.constants import (
    DEFAULT_THRESHOLD,
    LENGTH_PENALTY,
    TERM_FREQUENCY_SATURATION,
)
from lexmatch.models.entry import Entry
from lexmatch.stopwords import STOPWORDS
from lexmatch.text import normalize, query_terms


class Index:
    """A BM25 index over the owner's answers.

    BM25 in preference to plain TF-IDF for one practical reason: its length
    normalization stops a single long answer from dominating every query
    simply by containing more words.
    """

    def __init__(self, entries: list[Entry], threshold: float = DEFAULT_THRESHOLD) -> None:
        self.entries: list[Entry] = entries
        self.threshold: float = threshold
        self._documents: list[list[str]] = [entry.terms() for entry in entries]
        self._phrases: list[list[str]] = [entry.asked_phrases() for entry in entries]
        self._lengths: list[int] = [len(document) for document in self._documents]
        self._average_length: float = (
            sum(self._lengths) / len(self._lengths) if self._lengths else 0.0
        )
        self._term_counts: list[dict[str, int]] = []
        self._inverse_document_frequency: dict[str, float] = {}
        self._build_statistics()

    def score(self, query: str) -> list[tuple[float, Entry]]:
        """Score every entry against the query, best first."""
        tokens = query_terms(query)
        if not tokens or not self.entries:
            return []
        ceiling = self._score_ceiling(set(tokens))
        ranked = [
            (
                max(
                    self._bm25(position, set(tokens), ceiling),
                    self._phrase_score(position, query),
                ),
                entry,
            )
            for position, entry in enumerate(self.entries)
        ]
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        return ranked

    def answer(self, query: str) -> tuple[Entry | None, float]:
        """Best entry for the query, or None when nothing clears the bar."""
        ranked = self.score(query)
        if not ranked:
            return None, 0.0
        best_score, best_entry = ranked[0]
        if best_score < self.threshold:
            return None, best_score
        return best_entry, best_score

    def suggestions(self, limit: int = 5) -> list[str]:
        """Questions to offer in an empty chat box."""
        return [entry.question for entry in self.entries[:limit]]

    def _build_statistics(self) -> None:
        document_frequency: dict[str, int] = {}
        for document in self._documents:
            counts: dict[str, int] = {}
            for term in document:
                counts[term] = counts.get(term, 0) + 1
            self._term_counts.append(counts)
            for term in counts:
                document_frequency[term] = document_frequency.get(term, 0) + 1

        total = len(self._documents)
        # Standard BM25 IDF with the +1 guard, so a term present in every
        # entry scores zero rather than going negative.
        self._inverse_document_frequency = {
            term: math.log(1 + (total - seen + 0.5) / (seen + 0.5))
            for term, seen in document_frequency.items()
        }
        self._max_idf: float = max(self._inverse_document_frequency.values(), default=1.0)

    def _score_ceiling(self, unique_tokens: set[str]) -> float:
        """Compute the best score this query could achieve, to scale to 0..1."""
        per_term = self._max_idf * (TERM_FREQUENCY_SATURATION + 1) / TERM_FREQUENCY_SATURATION
        return per_term * len(unique_tokens) or 1.0

    def _bm25(self, position: int, unique_tokens: set[str], ceiling: float) -> float:
        counts = self._term_counts[position]
        length = self._lengths[position] or 1
        average = self._average_length or 1
        total = 0.0
        for term in unique_tokens:
            frequency = counts.get(term, 0)
            if not frequency:
                continue
            denominator = frequency + TERM_FREQUENCY_SATURATION * (
                1 - LENGTH_PENALTY + LENGTH_PENALTY * length / average
            )
            weight = self._inverse_document_frequency.get(term, 0.0)
            total += weight * frequency * (TERM_FREQUENCY_SATURATION + 1) / denominator
        return min(total / ceiling, 1.0)

    def _phrase_score(self, position: int, query: str) -> float:
        """How closely the query matches how the question was *asked*.

        Dice over all tokens, but only when the substantive words overlap.
        Without that guard "what is 2+2" scores 0.57 against "what is your
        job" purely on "what is" — filler shared by most questions.

        Queries made entirely of stopwords ("what do you do?") are why this
        exists: BM25 cannot rank them, because stopwords appear in every entry
        and carry no IDF. Those may match on filler, since filler is all they
        have.
        """
        query_tokens = set(normalize(query, keep_stopwords=True))
        if not query_tokens:
            return 0.0
        content_tokens = query_tokens - STOPWORDS
        best = 0.0
        for phrase in self._phrases[position]:
            # Phrases are non-empty: an alias that normalizes to nothing is
            # dropped when the index is built, so there is no empty set to
            # guard against here.
            phrase_tokens = set(phrase.split())
            if query_tokens == phrase_tokens:
                return 1.0
            if content_tokens and not (content_tokens & (phrase_tokens - STOPWORDS)):
                continue
            shared = len(query_tokens & phrase_tokens)
            if shared:
                dice = 2 * shared / (len(query_tokens) + len(phrase_tokens))
                best = max(best, dice)
        return best
