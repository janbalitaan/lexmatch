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
from lexmatch.models.outcome import Outcome
from lexmatch.models.reply import Reply
from lexmatch.models.tuning import Tuning
from lexmatch.negation import Negation
from lexmatch.questions import QuestionSplitter
from lexmatch.text import normalize


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
        # Entries are expanded but not typo-corrected. Correction exists to
        # read a visitor's mistake; an entry is the thing being matched
        # against, so "correcting" it would be changing the index to suit a
        # guess. A misspelled entry is the owner's to fix.
        expand = self.tuning.synonyms.expand
        # Both sides go through the same map, so a short form in a query
        # meets a long form in an entry whichever one was written short.
        self._documents: list[list[str]] = [expand(entry.terms()) for entry in entries]
        self._phrases: list[list[str]] = [entry.asked_phrases() for entry in entries]
        self._lengths: list[int] = [len(document) for document in self._documents]
        self._average_length: float = (
            sum(self._lengths) / len(self._lengths) if self._lengths else 0.0
        )
        # Every term the index contains, which is what a mistyped query word
        # is compared against. Built once: a query corrects against the
        # vocabulary, not against a dictionary, so it can only ever be
        # corrected toward something this index could answer.
        self._vocabulary: frozenset[str] = frozenset(
            term for document in self._documents for term in document
        )
        self._term_counts: list[dict[str, int]] = []
        self._inverse_document_frequency: dict[str, float] = {}
        self._build_statistics()

    def score(self, query: str) -> list[tuple[float, Entry]]:
        """Score every entry against the query, best first."""
        tokens = self._prepare_query(query, keep_stopwords=False)
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

    def reply(self, query: str) -> Reply:
        """Answer a query, or say which of the three ways it could not be.

        `answer()` returns a pair, which is enough to know whether anything
        matched. It is not enough to behave like a chatbot, because the ways
        a query fails need different things said:

            nothing matched       "I don't know that. Try one of these."
            two matched equally   "Which did you mean — design or review?"
            a negative question   the match is the opposite of the answer

        Collapsing those into `(None, 0.0)` is how a bot comes to answer
        about design rates when it was asked about rates.
        """
        ranked = self.score(query)
        if not ranked:
            return Reply(outcome=Outcome.UNANSWERED)
        best_score, best = ranked[0]

        if best_score < self.threshold:
            # Offer the near misses rather than the first entries in the
            # list: a question that scored nothing against everything gets
            # the index's own order, but one that nearly matched gets what
            # it nearly matched.
            return Reply(
                outcome=Outcome.UNANSWERED,
                score=best_score,
                suggestions=self._near_misses(ranked),
            )

        if Negation.disagree(query, best.question):
            return Reply(
                outcome=Outcome.NEGATED,
                entry=best,
                score=best_score,
                alternatives=(best,),
            )

        contenders = self._contenders(ranked, best_score)
        if len(contenders) > 1:
            return Reply(
                outcome=Outcome.AMBIGUOUS,
                score=best_score,
                alternatives=contenders,
                suggestions=tuple(entry.question for entry in contenders),
            )
        return Reply(outcome=Outcome.ANSWERED, entry=best, score=best_score)

    def _contenders(
        self, ranked: list[tuple[float, Entry]], best_score: float
    ) -> tuple[Entry, ...]:
        """Return the entries scoring within the ambiguity margin of the best."""
        margin = self.tuning.ambiguity_margin
        return tuple(
            entry
            for score, entry in ranked
            if score >= self.threshold and best_score - score <= margin
        )

    def _near_misses(
        self, ranked: list[tuple[float, Entry]], limit: int = 3
    ) -> tuple[str, ...]:
        """Return the questions a failed query came closest to.

        Falls back to the index's own order when nothing scored at all,
        because a query with no overlap has no near miss and the first few
        questions are at least an honest menu.
        """
        scored = [entry.question for score, entry in ranked[:limit] if score > 0]
        return tuple(scored or self.suggestions(limit=limit))

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
        strict = self._answer_each(QuestionSplitter.split(message))
        loose = self._answer_each(QuestionSplitter.split_loosely(message))
        # The loose split only wins by finding strictly more answers, which
        # is evidence the parts were separate questions after all. "comp and
        # notice period" has no interrogative in its second half, so the
        # strict rule keeps it whole and answers one of the two; the loose
        # one answers both. "remote and hybrid work" splits into halves that
        # answer the same entry, so nothing is gained and the strict reading
        # survives.
        return loose if len(loose) > len(strict) else strict

    def _answer_each(self, questions: list[str]) -> list[tuple[Entry, float]]:
        """Answer each question, in order, without repeating an entry."""
        found: list[tuple[Entry, float]] = []
        seen: set[int] = set()
        for question in questions:
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
        # The same two readings `answers` weighs, so the two agree about
        # what the message contained.
        strict = QuestionSplitter.split(message)
        loose = QuestionSplitter.split_loosely(message)
        chosen = (
            loose if len(self._answer_each(loose)) > len(self._answer_each(strict)) else strict
        )
        return [q for q in chosen if self.answer(q)[0] is None]

    def suggestions(self, limit: int = 5) -> list[str]:
        """Questions to offer in an empty chat box, or after a refusal.

        Small talk is excluded. Offering "hello" and "thanks" to somebody who
        just asked something the index could not answer is worse than
        offering nothing — it reads as not having understood that they asked
        a question at all. They are recognized by the `smalltalk` tag that
        `SmallTalk.entries` sets.

        Falls back to including them only if there is nothing else, so an
        index of small talk alone still suggests something.
        """
        content = [entry for entry in self.entries if "smalltalk" not in entry.tags]
        offered = content or self.entries
        return [entry.question for entry in offered[:limit]]

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

    def _comparable(self, tokens: set[str]) -> set[str]:
        """Drop query words that appear in no entry at all.

        Dice is `2|A∩B| / (|A|+|B|)`. A word in no entry can never be in any
        intersection, so counting it in `|A|` lowers every score equally —
        noise with no signal, and the lower the score the more likely a right
        answer falls under the threshold.

        It shows up most with a paraphrase. `{"how much": "rate"}` expands
        "how much do you charge for design" and keeps the originals, so
        "much" and "charge" ride along matching nothing: the correct entry
        ranked first either way but scored 0.400 instead of 0.612, and the
        threshold is 0.45. The right answer was there and refused.

        Also catches a typo that could not be corrected, and a word from a
        question the index was never given.

        Used for the Dice ratio only. The content-overlap guard still runs
        on the unfiltered set, because an unknown word is evidence that the
        query is about something the index does not cover — filtering it out
        before the guard turned an off-topic question into a stopword-only
        one, which is the one shape allowed to match on filler.

        Everything is kept when nothing is recognized, because a query made
        only of unknown words has nothing else to be compared on and scoring
        zero against everything is the honest outcome either way.
        """
        known = {token for token in tokens if token in self._vocabulary}
        return known or tokens

    def _prepare_query(self, query: str, keep_stopwords: bool) -> list[str]:
        """Turn raw text into the tokens scoring compares.

        The order is the whole of it, and getting it wrong is silent.

        **Normalize keeping stopwords, then correct, then expand, then strip.**

        Stripping first destroyed a phrase synonym made of stopwords: "how
        much" is two stopwords, so `{"how much": "rate"}` never fired and
        "how much do you charge" stayed unanswered — the exact paraphrase
        that phrase keys exist for.

        Correcting before expanding, because a mistyped short form has to
        become the short form first: the synonym map is keyed on "wfh", so
        "wfhh" expands to nothing if the order is reversed.
        """
        words = normalize(query, keep_stopwords=True)
        corrected = self.tuning.corrections.apply(words, self._vocabulary)
        expanded = self.tuning.synonyms.expand(corrected)
        if keep_stopwords:
            return expanded
        stripped = [word for word in expanded if word not in self.tuning.stopwords]
        # A query of nothing but stopwords — "what do you do?" — has every
        # word removed, and the index holds stopwords too, so the unstripped
        # form is the one that can still match.
        return stripped or expanded

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

        Words the index has never heard of are dropped first — see
        `_comparable`.
        """
        asked = set(self._prepare_query(query, keep_stopwords=True))
        if not asked:
            return 0.0
        # The guard below runs on what was *asked*, including words the index
        # has never heard of. Those words are the evidence that the query is
        # about something else: filtering them out first turned an off-topic
        # question into a stopword-only one — the single shape allowed to
        # match on filler alone — and "what is the capital of France" then
        # matched "What is your rate" on "what is". Eighteen tests caught it.
        content_tokens = asked - self.tuning.stopwords
        # Dice runs on what is *comparable*, but only when there is content
        # to compare. A word in no entry can never be in an intersection, so
        # counting it in the denominator lowers every score equally — noise
        # with no signal.
        #
        # For a query of nothing but stopwords the filler *is* the signal:
        # "who are you" and "what do you do" differ only in their filler, and
        # dropping the unknown word shrank the denominator and pushed a
        # filler-only match from 0.444 to 0.500 — over the threshold, so a
        # bare index began answering "who are you" with whatever came first.
        query_tokens = self._comparable(asked) if content_tokens else asked
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
