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

from lexmatch.composer import Composer
from lexmatch.constants import AMBIGUITY_ALTERNATIVES, SMALL_TALK_TAG
from lexmatch.models.entry import Entry
from lexmatch.models.outcome import Outcome
from lexmatch.models.reply import Reply
from lexmatch.models.tuning import Tuning
from lexmatch.negation import Negation
from lexmatch.questions import QuestionSplitter
from lexmatch.text import normalize

# Below this, a total IDF weight is indistinguishable from zero and the
# weighted ratio would divide by it. Reached only by a query of nothing but
# stopwords, which falls back to counting tokens.
_NEGLIGIBLE = 1e-9

# Two distinct answers from one message means it really asked two things.
_TWO_QUESTIONS = 2


def _phrasing_tokens(entry: Entry) -> set[str]:
    """Every word an entry's own question and aliases use."""
    tokens: set[str] = set()
    for phrase in (entry.question, *entry.aliases):
        tokens |= set(normalize(phrase, keep_stopwords=True))
    return tokens


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
        composer: type[Composer] | None = None,
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
        # A class rather than an instance: every method on it is a
        # classmethod, so there is no state to carry and subclassing is the
        # whole extension mechanism.
        self._composer: type[Composer] = composer or Composer
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
        # Stemming folds inflections onto one token, and runs last so the
        # synonym map stays keyed on words a developer would write. Both the
        # index and the query go through `Tuning.fold`, so the two agree.
        fold = self.tuning.fold
        self._documents: list[list[str]] = [fold(expand(entry.terms())) for entry in entries]
        self._phrases: list[list[str]] = [entry.asked_phrases() for entry in entries]
        # The phrases as token sets, and their weight. Both are properties of
        # the index, so computing them per query meant splitting every phrase
        # of every entry on every reply and summing its weight again.
        self._phrase_tokens: list[list[frozenset[str]]] = [
            [frozenset(fold(phrase.split())) for phrase in phrases] for phrases in self._phrases
        ]
        self._lengths: list[int] = [len(document) for document in self._documents]
        # Filled by `_build_statistics`, once the stopword set and the
        # weights it needs both exist.
        self._phrase_content: list[list[frozenset[str]]] = []
        self._phrase_content_mass: list[list[float]] = []
        # Which words each entry's own phrasings use, for holding a small-talk
        # entry back from a substantive question. Built here rather than per
        # query: deriving it in the scoring loop normalized every phrase of
        # every entry on every reply, and took one reply against 5000 entries
        # from 2.4 ms to 27 ms.
        self._social_tokens: list[frozenset[str]] = [
            frozenset(fold(list(_phrasing_tokens(entry))))
            if SMALL_TALK_TAG in entry.tags
            else frozenset()
            for entry in entries
        ]
        self._average_length: float = (
            sum(self._lengths) / len(self._lengths) if self._lengths else 0.0
        )
        # Every term the index contains, which is what a mistyped query word
        # is compared against. Built once: a query corrects against the
        # vocabulary, not against a dictionary, so it can only ever be
        # corrected toward something this index could answer.
        # Unstemmed, because this is what a mistyped word is compared
        # against: "notce" has to reach "notice", and comparing it to the
        # stem "notic" is a worse match on a word nobody wrote.
        self._vocabulary: frozenset[str] = frozenset(
            term for entry in entries for term in expand(entry.terms())
        )
        # The same terms folded, for the prefix rule in `Morphology`. It has
        # to compare like with like: "secure" folds to "secur", which is a
        # prefix of "security", while the unfolded "secure" is not a prefix
        # of anything because of its "e".
        self._stemmed_vocabulary: frozenset[str] = frozenset(
            self.tuning.fold(list(self._vocabulary))
        )
        # The stopwords as the scorer will meet them. Stemming is applied to
        # tokens but the stopword set is written in whole words, so the two
        # stopped lining up: "there" folds to "ther", which is in no stopword
        # list, so "hey there" turned into a greeting plus a content word that
        # no greeting covers — and was refused at 0.000 where it had scored
        # 1.000. The originals are kept alongside, because an unfolded token
        # still has to be recognized.
        self._stopwords: frozenset[str] = self.tuning.stopwords | frozenset(
            self.tuning.fold(list(self.tuning.stopwords))
        )
        self._term_counts: list[dict[str, int]] = []
        self._inverse_document_frequency: dict[str, float] = {}
        self._build_statistics()

    def score(self, query: str) -> list[tuple[float, Entry]]:
        """Score every entry against the query, best first.

        The query is prepared **once**. It used to be prepared inside
        `_phrase_score`, which runs per entry — so normalizing, correcting
        and expanding happened once per entry rather than once per query.
        Profiled over 5,000 entries that was 200,000 calls for ten responses
        and 62 ms each; it is linear in entries either way, but with a
        constant nobody needed.
        """
        asked = set(self._prepare_query(query))
        if not asked or not self.entries:
            return []
        content = asked - self._stopwords
        # BM25 sees the substantive words only. Stopwords appear in every
        # entry and carry no IDF, exactly as `_phrase_score` documents — so
        # ranking by them is ranking by noise. An earlier version fed BM25
        # the unstripped query whenever stripping left nothing, and "who are
        # you" scored 0.921 against "Are you open to remote work" once the
        # ceiling became reachable, because filler was all there was to
        # reach.
        unique = content
        ceiling = self._score_ceiling(unique)
        specificity = self._specificity(unique)
        # For a query of nothing but stopwords the filler *is* the signal:
        # "who are you" and "what do you do" differ only in their filler, so
        # dropping an unknown word shrinks the denominator and pushes a
        # filler-only match over the threshold — measured at 0.444 to 0.500,
        # which had a bare index answering "who are you" with whatever came
        # first.
        comparable = self._comparable(asked) if content else asked
        ranked = [
            (
                max(
                    self._bm25(position, unique, ceiling) * specificity,
                    self._phrase_score(position, comparable, content, asked),
                )
                * self._social_scale(position, content),
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
        # Only a message that actually splits can be compound, and the check
        # below costs a full scoring pass per part. Asking the splitter first
        # is two regular expressions; `_best_reading` on a single question
        # scored every entry two or three times for nothing, which took a
        # reply against 5000 entries from 18 ms to 36.
        if not QuestionSplitter.looks_compound(query):
            return self._reply_to_one(query)

        answered = self._best_reading(query)[1]
        distinct = {id(entry) for entry, _ in answered}
        if len(distinct) >= _TWO_QUESTIONS:
            return self._compound_reply(answered)
        # Scored only now. When the strict split is a single part it *is* the
        # whole string, so `_best_reading` has already scored it — computing
        # it up front scored every entry twice and took a compound message
        # against 5000 entries to 41.6 ms.
        whole = self._reply_to_one(query)
        # A greeting is not a rescue. "Good afternoon. What is the largest
        # system you have personally designed?" splits into a pleasantry that
        # answers and a question that does not, and answering it "Hello" at
        # 1.000 is worse than refusing — it reads as not having noticed the
        # question. So a rescue needs something substantive to rescue with.
        substantive = any(SMALL_TALK_TAG not in entry.tags for entry, _ in answered)
        rescues = substantive and not whole.answered
        if not rescues:
            # The message splits, but reading it in parts says nothing the
            # whole string did not. Two conditions, and each is a measured
            # case rather than a precaution.
            #
            # **Two distinct answers** means it really was two questions:
            # "yoe and tech stack?" tied at 0.586 between the experience and
            # stack entries and asked which was meant, while `answers()` had
            # already resolved it to both. Ambiguity is *one* question
            # matching two entries; asking which was meant when two were
            # asked answers neither.
            #
            # **A rescue** is a part that answers where the whole string
            # would not: "I don't need visa sponsorship, what's the stack?"
            # was reported NEGATED, because the first clause's "not" was read
            # against the second clause's answer.
            #
            # Overriding a whole-string reply that *did* answer costs more
            # than it gains — it fell from 65.9% to 61.0% across fifteen
            # simulated visitors, because a message that splits is usually
            # still one question.
            return whole
        return self._compound_reply(answered)

    def _compound_reply(self, answered: list[tuple[Entry, float]]) -> Reply:
        """Build one reply out of the answers to a message's parts.

        The substantive part leads, not whichever came first. "Hi — do you
        have capacity for three months?" answers the greeting and the
        question both, and headlining the greeting reads as having ignored
        the question: two such messages were answered "Hello." at 1.000 while
        the real answer sat in `alternatives`.
        """
        ordered = sorted(answered, key=self._social_last)
        first, first_score = ordered[0]
        return Reply(
            outcome=Outcome.ANSWERED,
            entry=first,
            score=first_score,
            alternatives=tuple(entry for entry, _ in ordered[1:]),
        )

    @staticmethod
    def _social_last(answered: tuple[Entry, float]) -> tuple[bool, float]:
        """Sort key putting small talk after everything else.

        Within each group the higher score comes first, so the strongest
        substantive answer leads and the pleasantry trails.
        """
        entry, score = answered
        return (SMALL_TALK_TAG in entry.tags, -score)

    def _reply_to_one(self, query: str) -> Reply:
        """Answer a query read as a single question.

        Separate from `reply` so the compound check happens once, at the top.
        `_best_reading` answers each part to decide which reading to keep, so
        a compound check inside this method would call itself through that —
        which it did, as unbounded recursion.
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
            if best_score < self.tuning.ambiguity_floor:
                # A tie among weak matches is not ambiguity, it is a question
                # that was not understood. Measured over thirty simulated
                # visitors, "what do you work on" tied at 0.537 against "Are
                # you open to remote work" and "Do you need visa
                # sponsorship" — on the word "work" plus filler — and asking
                # which was meant read as nonsense. Reported as unanswered
                # with the contenders offered, which lets the visitor choose
                # rather than taking a one-in-four guess.
                return Reply(
                    outcome=Outcome.UNANSWERED,
                    score=best_score,
                    suggestions=tuple(
                        entry.question for entry in contenders[:AMBIGUITY_ALTERNATIVES]
                    ),
                )
            offered = contenders[:AMBIGUITY_ALTERNATIVES]
            return Reply(
                outcome=Outcome.AMBIGUOUS,
                score=best_score,
                alternatives=offered,
                suggestions=tuple(entry.question for entry in offered),
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
        _, found = self._best_reading(message)
        return found

    def _best_reading(self, message: str) -> tuple[list[str], list[tuple[Entry, float]]]:
        """Choose between the strict and loose splits, and answer the winner.

        `answers()` and `unanswered()` need the same decision, and each used
        to make it separately — so one `respond()` scored every entry four
        times over. The decision and its answers are produced together here.
        """
        strict_parts = QuestionSplitter.split(message)
        loose_parts = QuestionSplitter.split_loosely(message)
        strict = self._answer_each(strict_parts)
        if len(loose_parts) == len(strict_parts):
            # The same reading, so there is no second pass worth running.
            return strict_parts, strict
        loose = self._answer_each(loose_parts)
        # The loose split only wins by finding strictly more answers, which
        # is evidence the parts were separate questions after all. "comp and
        # notice period" has no interrogative in its second half, so the
        # strict rule keeps it whole and answers one of the two; the loose
        # one answers both. "remote and hybrid work" splits into halves that
        # answer the same entry, so nothing is gained and the strict reading
        # survives.
        if len(loose) > len(strict):
            return loose_parts, loose
        return strict_parts, strict

    def _answer_each(self, questions: list[str]) -> list[tuple[Entry, float]]:
        """Answer each question, in order, without repeating an entry.

        Goes through `reply()` rather than `answer()`. Using the simpler one
        bypassed every check `reply()` exists for, on exactly the messages
        most likely to need them: an ambiguous part of a compound message
        was answered with the first of its contenders, and a negative part
        was answered affirmatively. `answers()` looked like it worked while
        quietly skipping the safety it was built on top of.
        """
        found: list[tuple[Entry, float]] = []
        seen: set[int] = set()
        for question in questions:
            reply = self._reply_to_one(question)
            if not reply.answered or reply.entry is None:
                continue
            if id(reply.entry) in seen:
                continue
            seen.add(id(reply.entry))
            found.append((reply.entry, reply.score))
        return found

    def respond(self, message: str) -> str:
        """Answer a whole message in one sentence, however it is shaped.

        The top of the library. Splits a compound message, replies to each
        part, and writes the result as something a person would say — so a
        caller with a chat box needs one call rather than the four it took to
        assemble this by hand.

        Every sentence in the result is either an entry's own answer or one
        of `Composer`'s fixed phrases. Nothing is invented, so a response can
        say nothing the owner did not write.

        For a voice of your own, subclass `Composer` and pass it as
        `composer`; for the structure behind the sentence, use `reply()` and
        `answers()` directly.
        """
        composer = self._composer
        chosen, answers = self._best_reading(message)
        if answers:
            answered = {id(entry) for entry, _ in answers}
            missed = [
                question
                for question in chosen
                if (found := self.reply(question)).entry is None
                or id(found.entry) not in answered
            ]
            return composer.compose(answers, missed)
        # Nothing answered. A single question gets the reason — ambiguous,
        # negative, or simply unknown — which a list of zero answers cannot
        # carry.
        return composer.compose_reply(self.reply(message))

    def unanswered(self, message: str) -> list[str]:
        """Which questions in a message found no answer.

        The companion to `answers()`. A message asking three things where two
        are covered should say so rather than reply to two and leave the
        third unmentioned — that reads as having been understood.

            replies = index.answers(message)
            missed = index.unanswered(message)
        """
        chosen, _ = self._best_reading(message)
        return [question for question in chosen if not self.reply(question).answered]

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
        # The phrases with their stopwords removed, and the weight of what is
        # left. Both are properties of the index, and deriving them inside the
        # ranking loop subtracted a hundred-word set and re-summed its weights
        # for every phrase of every entry on every reply — 18 ms a reply
        # against 5000 entries became 38.
        idf = self._inverse_document_frequency
        self._phrase_content = [
            [tokens - self._stopwords for tokens in per_entry]
            for per_entry in self._phrase_tokens
        ]
        self._phrase_content_mass = [
            [sum(idf.get(token, 0.0) for token in tokens) for tokens in per_entry]
            for per_entry in self._phrase_content
        ]

    def _social_scale(self, position: int, content_tokens: set[str]) -> float:
        """Zero for a small-talk entry answering a substantive question.

        Social phrasings are short, and the length penalty favours short
        entries, so a message that merely contains a pleasantry was being
        answered by one. Measured over fifteen simulated visitors: "is the
        pay good" scored 1.000 against the greeting entry because "good"
        matches "good morning", and "do you care about the frontend at all"
        scored 0.957 against the farewell because "care" matches "take care".
        Both are real questions that happen to contain a social word.

        A small-talk entry may only answer when the message is small talk:
        every substantive word in the query has to be one the entry's own
        phrasings use. "hello" and "yo" pass. "hi do u do consulting" does
        not, because "consulting" is nowhere in the greeting phrasings — and
        suppressing it is what lets the consulting entry answer instead.

        Entries that are not small talk are unaffected, and which entries
        count is `SMALL_TALK_TAG`, so a custom set can opt in or out. The
        phrasings are tokenized at build time, in `_social_tokens`.
        """
        covered = self._social_tokens[position]
        if not covered or not content_tokens:
            return 1.0
        # An acknowledgement is social, not substantive, so it does not count
        # against small talk. "great, thanks" is one unit — a comma is not a
        # terminator — and "great" is in none of the thanks phrasings, which
        # suppressed a reply that was entirely correct. "is the pay good" is
        # still suppressed, because "pay" survives this.
        uncovered = (
            content_tokens - covered - self._stopwords - QuestionSplitter.ACKNOWLEDGEMENTS
        )
        return 0.0 if uncovered else 1.0

    def _weighted_dice(
        self,
        shared: set[str],
        query_tokens: set[str],
        phrase_tokens: frozenset[str] | set[str],
        query_mass: float,
        phrase_mass: float | None,
    ) -> float:
        """Dice over the tokens' *weight* rather than their count.

        Counting tokens equally treats "how do you" exactly like "refactor",
        and most questions in an index share a form. Measured over eleven
        professional roles, "how do you mentor juniors" scored **1.000**
        against the small-talk entry "how are you" — two of three tokens
        shared, none of them meaning anything — and "how do you decide when
        to refactor" scored 0.890 against "How do you decide build versus
        buy" on the shared "how do you decide".

        Weighting by inverse document frequency is the same ratio over the
        information each token carries: a word in every entry contributes
        almost nothing to either side, so a shared question form no longer
        looks like a shared subject.

        The zero-weight fallback counts tokens instead. The `+ 1` guard in
        the inverse document frequency means a term in every entry still
        scores about 0.29, so this is unreachable with the built-in weights —
        it is here because the weights are a plain mapping a developer can
        replace, and one that returns zero for a token would otherwise divide
        by it.
        """
        idf = self._inverse_document_frequency
        if phrase_mass is None:
            phrase_mass = sum(idf.get(token, 0.0) for token in phrase_tokens)
        total_mass = query_mass + phrase_mass
        if total_mass <= _NEGLIGIBLE:
            return 2 * len(shared) / (len(query_tokens) + len(phrase_tokens))
        shared_mass = sum(idf.get(token, 0.0) for token in shared)
        return 2 * shared_mass / total_mass

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

    def _prepare_query(self, query: str) -> list[str]:
        """Turn raw text into tokens, keeping the stopwords.

        The order is the whole of it, and getting it wrong is silent.

        **Normalize keeping stopwords, then correct, then expand.** Stripping
        first destroyed a phrase synonym made of stopwords: "how much" is two
        stopwords, so `{"how much": "rate"}` never fired on "how much do you
        charge" — the exact paraphrase phrase keys exist for.

        Correcting before expanding, because a mistyped short form has to
        become the short form first: the synonym map is keyed on "wfh", so
        "wfhh" expands to nothing if the order is reversed.

        Stopwords are stripped by the caller rather than here, because the
        two scorers want different sets — BM25 the substantive words, the
        phrase scorer everything. It used to return a stripped list with a
        fall-back to the unstripped one when stripping left nothing, and
        that fall-back silently fed BM25 a query of pure filler.
        """
        words = normalize(query, keep_stopwords=True)
        corrected = self.tuning.corrections.apply(words, self._vocabulary)
        folded = self.tuning.fold(self.tuning.synonyms.expand(corrected))
        # Last, and in stem space. A word the index does not hold may be the
        # start of one it does — "senior" of "seniority" — and stemming has
        # deliberately left that alone, because the endings it would have to
        # strip are the ones that change what a word means.
        if self.tuning.morphology is None:
            return folded
        return self.tuning.morphology(folded, self._stemmed_vocabulary)

    def _score_ceiling(self, unique_tokens: set[str]) -> float:
        """Compute the best score this query could achieve, to scale to 0..1.

        Each term contributes **its own** maximum, not the index's. The
        ceiling used to be `max_idf * number_of_terms`, which assumes every
        query term is as rare as the rarest term in the index — so a common
        word like "work" was counted at a weight it could never earn, and
        the ceiling grew with each word while the achievable score did not.

        Measured on a question whose discriminating word was present
        throughout:

            'advisory'                      1.000
            'advisory work'                 0.512
            'do you take on advisory work'  0.341

        The same keyword, scoring worse the more naturally it was asked —
        which is backwards, because people write sentences. Summing each
        term's own ceiling makes the normalization reachable.

        A term the index has never seen contributes nothing to either side,
        so it neither helps nor penalizes. That is deliberate and was
        measured twice, because the alternative is tempting: an unknown word
        is invisible, which leaves "do you like working alone" scoring 1.000
        against "Are you open to remote work?" on the one word they share.

        Both ways of charging for it made the library worse across 133
        questions from thirty-seven simulated askers:

            ignoring unknown words (this)        81.2%
            charging a linear cost for them      73.7%
            counting them at a zero-document
            frequency, which is the highest
            weight the formula gives             69.9%

        The reason is structural. In a question set small enough to hand
        write, most words in a naturally phrased question are absent from
        every entry — they are conversational, not substantive. Charging for
        an unknown word therefore charges for natural phrasing, and that is
        the defect the reachable ceiling above exists to fix. `Tuning.
        unknown_word_cost` is still there for an index where a wrong answer
        is worse than no answer.
        """
        saturation = self.tuning.saturation
        scale = (saturation + 1) / saturation
        total = sum(
            self._inverse_document_frequency.get(term, 0.0) * scale for term in unique_tokens
        )
        return total or 1.0

    def _specificity(self, unique_tokens: set[str]) -> float:
        """How confident any answer to this query is allowed to be.

        BM25 is normalized against what the query could achieve, which is
        the right scale and says nothing about whether the query was worth
        asking. A query whose only content word is common matches 100% of
        what was askable and still carries almost no information.

        Measured in this index, where the rarest term scores 2.77:

            'advisory'              2.77   as specific as anything gets
            'what is your rate'     2.77
            'overlap with EST'      2.77
            'what do you work on'   1.31   one common word
            'whats the weather'     0.00   nothing the index knows

        Without this the third scored 1.000 against every entry containing
        "work" and asked which of three unrelated questions was meant.
        Scaling by the query's own informativeness puts it at 0.47 — over
        the threshold, under the ambiguity floor, so the contenders are
        offered rather than one being guessed at.

        Capped at 1, so a long specific query is not rewarded twice.

        Multiplied by how much of the query the index recognized at all. A
        word the index has never seen has no inverse document frequency, so
        it contributed nothing to the ceiling either — which made it
        *invisible*, and left any query perfectly satisfiable by matching
        only the words it happened to share:

            'what dashboards do you build'   1.000 "How do you decide build
                                                    versus buy?"
            'would you be a technical
             cofounder'                      1.000 "How do you approach
                                                    technical debt?"

        Both scored full marks on one shared word while the word the question
        was actually about — "dashboards", "cofounder" — was discarded before
        anything was scored. Recognizing half of a question is not grounds
        for a confident answer to it.
        """
        mass = sum(self._inverse_document_frequency.get(term, 0.0) for term in unique_tokens)
        if not unique_tokens or self._max_idf <= 0:
            # No substantive words, or an index where every term is in every
            # entry. Either way there is nothing for BM25 to be confident
            # about, and the phrase scorer is what speaks for such a query.
            return 0.0
        return min(mass / self._max_idf, 1.0) * self._recognized(unique_tokens)

    def _recognized(self, unique_tokens: set[str]) -> float:
        """Return what fraction of the query's content words the index has seen.

        Counted rather than weighted, because an unknown word has no weight
        to count — that is the whole problem. Tuned by
        `Tuning.unknown_word_cost`: 1.0 charges the full fraction, 0.0
        restores the old behavior of ignoring unknown words.
        """
        known = sum(1 for term in unique_tokens if term in self._inverse_document_frequency)
        fraction = known / len(unique_tokens)
        cost = self.tuning.unknown_word_cost
        return fraction * cost + (1.0 - cost)

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

    def _phrase_score(
        self,
        position: int,
        query_tokens: set[str],
        content_tokens: set[str],
        asked: set[str],
    ) -> float:
        """How closely the query matches how the question was *asked*.

        Dice over all tokens, but only when the substantive words overlap.
        Without that guard "what is 2+2" scores 0.57 against "what is your
        job" purely on "what is" — filler shared by most questions.

        Queries made entirely of stopwords ("what do you do?") are why this
        exists: BM25 cannot rank them, because stopwords appear in every
        entry and carry no IDF. Those may match on filler, since filler is
        all they have.

        Both token sets are prepared by the caller, once per query rather
        than once per entry. They are different sets on purpose:

        `content_tokens` is what was *asked*, minus stopwords, including
        words the index has never heard of — those words are the evidence
        that a question is off-topic. Filtering them out before the guard
        turned "what is the capital of France" into a stopword-only query,
        the one shape allowed to match on filler, and it matched "What is
        your rate" on "what is".

        `query_tokens` is what is *comparable*: a word in no entry can never
        be in an intersection, so counting it in Dice's denominator lowers
        every score equally.
        """
        if not query_tokens:
            return 0.0
        idf = self._inverse_document_frequency
        query_content = query_tokens & content_tokens
        query_mass = sum(
            idf.get(token, 0.0) for token in (query_content if content_tokens else query_tokens)
        )
        best = 0.0
        # Phrases are non-empty: an alias that normalizes to nothing is
        # dropped when the index is built, so there is no empty set to guard
        # against here. The tokens, their content and its weight are all
        # built with the index.
        for phrase_tokens, phrase_content, phrase_mass in zip(
            self._phrase_tokens[position],
            self._phrase_content[position],
            self._phrase_content_mass[position],
            strict=True,
        ):
            # The constant described this guard but was never read: the
            # requirement was hard-coded at "any overlap at all", so a
            # caller who raised MIN_CONTENT_OVERLAP got no change. Reading it
            # is what makes it tunable, and raising it to 2 is the lever for
            # an index whose entries share a lot of vocabulary.
            shared_content = content_tokens & phrase_content
            if content_tokens and len(shared_content) < self.tuning.minimum_overlap:
                continue
            # The exact-match shortcut is checked *after* the guard and
            # against what was **asked**, not against what survived
            # filtering. Both were wrong before, and together they scored
            # "how do you mentor juniors" at 1.000 against the small-talk
            # alias "how do you do": "mentor" and "juniors" are not in this
            # index's vocabulary, so the comparable set was filtered down to
            # the filler `{how, do, you}` — which equalled that alias
            # exactly, and the shortcut returned before the guard could
            # object that no substantive word was shared.
            if asked == phrase_tokens:
                return 1.0
            # Content decides a content question. Stopwords stay in the
            # comparison only for a query that has nothing else, which is
            # what the arrangement-is-the-signal case needs.
            #
            # They carry real weight in a small index — "how" and "do" score
            # 0.66 and 0.60 against twenty-five entries — so including them
            # let a shared *form* outrank a shared subject. Measured: "how do
            # standups work for you" scored 0.669 against "How do you
            # estimate work?" on {how, do, you, work}, beating the agile
            # entry's 0.637 on "standup" alone — and "standup" is an alias of
            # the agile entry and carries twice the weight of "work".
            if content_tokens:
                query_side, phrase_side = query_content, phrase_content
                side_mass = phrase_mass
            else:
                query_side, phrase_side = query_tokens, phrase_tokens
                side_mass = None
            shared = query_side & phrase_side
            if shared:
                best = max(
                    best,
                    self._weighted_dice(shared, query_side, phrase_side, query_mass, side_mass),
                )
        return best
