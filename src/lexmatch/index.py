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

from lexmatch.models.entry import Entry
from lexmatch.models.tuning import Tuning
from lexmatch.questions import QuestionSplitter
from lexmatch.text import normalize, query_terms


class Index:
    """A BM25 index over the owner's answers.

    BM25 in preference to plain TF-IDF for one practical reason: its length
    normalization stops a single long answer from dominating every query
    simply by containing more words.
    """

    def __init__(
        self,
        entries: list[Entry],
        threshold: float | None = None,
        tuning: Tuning | None = None,
    ) -> None:
        """Build an index over these entries.

        `tuning` replaces every number the scorer uses — the threshold, the
        term-frequency saturation, the length penalty, the minimum content
        overlap, and the stopword list. See `lexmatch.models.tuning`.

        `threshold` stays for the common case of changing only that, and
        wins over `tuning.threshold` when both are given: a caller who named
        it explicitly meant it.
        """
        self.tuning: Tuning = tuning or Tuning()
        if threshold is not None:
            self.tuning = self.tuning.with_threshold(threshold)
        self.entries: list[Entry] = entries
        # Kept as a plain attribute because it was one, and reading
        # `index.threshold` is how callers already check what was configured.
        self.threshold: float = self.tuning.threshold
        expand = self.tuning.synonyms.expand
        # Both sides go through the same map, so a short form in a query
        # meets a long form in an entry whichever one was written short.
        self._documents: list[list[str]] = [expand(entry.terms()) for entry in entries]
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
        tokens = self.tuning.synonyms.expand(query_terms(query))
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

    def answers(self, message: str) -> list[tuple[Entry, float]]:
        """Answer every question in a message, in the order asked.

        A message asking two things scores *worse* against both than either
        would alone, because the phrase measure is an overlap ratio: doubling
        the query's length halves the proportion any one entry can share.
        Measured on "remote? rates? notice period?" the best entry reached
        0.480 and the other two 0.400 and 0.250 — so one got answered and two
        were silently dropped.

        Splitting first turns those into three questions that each score
        1.000.

        Returns one pair per question that found an answer, so a message with
        two questions and one answerable gets a list of one. An empty list
        means nothing was answerable, which is the same thing `answer()`
        reports with `None` — and a caller wanting the whole message treated
        as one question should still use `answer()`.

        Duplicates are collapsed: "rates? pricing?" are two questions with
        one answer, and saying it twice reads as a malfunction.
        """
        found: list[tuple[Entry, float]] = []
        seen: set[int] = set()
        for question in QuestionSplitter.split(message):
            entry, score = self.answer(question)
            if entry is None or id(entry) in seen:
                continue
            seen.add(id(entry))
            found.append((entry, score))
        return found

    def unanswered(self, message: str) -> list[str]:
        """Which questions in a message found no answer.

        The companion to `answers()`. A message asking three things where two
        are covered should say so rather than reply to two and leave the
        third unmentioned — that reads as having been understood.

            replies = index.answers(message)
            missed = index.unanswered(message)
        """
        return [
            question
            for question in QuestionSplitter.split(message)
            if self.answer(question)[0] is None
        ]

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
        saturation = self.tuning.saturation
        per_term = self._max_idf * (saturation + 1) / saturation
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
            saturation = self.tuning.saturation
            penalty = self.tuning.length_penalty
            denominator = frequency + saturation * (1 - penalty + penalty * length / average)
            weight = self._inverse_document_frequency.get(term, 0.0)
            total += weight * frequency * (saturation + 1) / denominator
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
        query_tokens = set(self.tuning.synonyms.expand(normalize(query, keep_stopwords=True)))
        if not query_tokens:
            return 0.0
        content_tokens = query_tokens - self.tuning.stopwords
        best = 0.0
        for phrase in self._phrases[position]:
            # Phrases are non-empty: an alias that normalizes to nothing is
            # dropped when the index is built, so there is no empty set to
            # guard against here.
            phrase_tokens = set(phrase.split())
            if query_tokens == phrase_tokens:
                return 1.0
            stopwords = self.tuning.stopwords
            # The constant described this guard but was never read: the
            # requirement was hard-coded at "any overlap at all", so a
            # caller who raised MIN_CONTENT_OVERLAP got no change. Reading it
            # is what makes it tunable, and raising it to 2 is the lever for
            # an index whose entries share a lot of vocabulary.
            shared_content = content_tokens & (phrase_tokens - stopwords)
            if content_tokens and len(shared_content) < self.tuning.minimum_overlap:
                continue
            shared = len(query_tokens & phrase_tokens)
            if shared:
                dice = 2 * shared / (len(query_tokens) + len(phrase_tokens))
                best = max(best, dice)
        return best
