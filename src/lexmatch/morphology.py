"""Relating a word to a longer word built from it.

Stemming folds inflection — "consulting" onto "consult", "rates" onto
"rate". It deliberately stops there, because the endings it leaves alone
change what a word is about: "payment" is not "pay" and "consultant" is not
"consulting", and merging those merges two entries that answer different
questions.

But an index does not always hold both forms, and then the distinction costs
an answer instead of protecting one. An index whose only term is "seniority"
cannot be reached by "are you a senior", and nothing reports the failure.

Typo correction does not bridge it either, and for a good reason: it compares
only words of a similar length, because a token is not a typo of something
three characters longer. "senior" and "seniority" differ by three.

So this is a separate mechanism with a stricter rule. A query word is treated
as the longer index word when it is a **prefix** of it and long enough to be
unambiguous.

Worth one question in 133 measured, which is a small gain honestly stated:
the cases it rescues are the ones where an index holds a derived form and not
its root, and how often that happens is a property of the question set rather
than of this code. It is cheap, it is guarded against ambiguity, and it costs
nothing when it does not fire.

    senior      ->  seniority
    secure      ->  security
    observe     ->  observability

A prefix rather than a similarity score, because that is what derivation
looks like in English — the word is built on the front of the longer one, and
requiring the whole of it keeps "measure" away from "metrics".
"""

from __future__ import annotations

from typing import ClassVar


class Morphology:
    """Maps a query word onto a longer index word built from it.

    Only ever lengthens, and only toward a word the index actually holds, so
    it cannot invent a term. Replace `SHORTEST_PREFIX` to change how much
    evidence it needs, or `STOP_AT` to protect a word from being extended.
    """

    #: How many characters a query word must have before it may be read as
    #: the start of a longer one.
    #:
    #: Swept against 133 measured questions, three through six scored
    #: identically (114 right, 6 wrong) and seven matched the mechanism being
    #: off entirely (113). So the measurement does not choose between them,
    #: and five is a judgement rather than a finding: it is the point at
    #: which a shared prefix stops being plausibly coincidental, and the
    #: question sets happen not to contain the cases that would separate it
    #: from four. "plan" reaching "planet" and "cost" reaching "costume" are
    #: the kind of thing it is guarding against, and neither appears above.
    SHORTEST_PREFIX: ClassVar[int] = 5

    #: Words that are complete in themselves, so a longer word starting the
    #: same way is a different word rather than a derivation of this one.
    STOP_AT: ClassVar[frozenset[str]] = frozenset(
        {
            "about",
            "after",
            "again",
            "among",
            "based",
            "being",
            "below",
            "could",
            "every",
            "first",
            "great",
            "least",
            "might",
            "other",
            "quite",
            "shall",
            "since",
            "still",
            "their",
            "there",
            "these",
            "those",
            "under",
            "until",
            "where",
            "which",
            "while",
            "would",
        }
    )

    @classmethod
    def extend(cls, token: str, vocabulary: frozenset[str]) -> str:
        """Return the index word this token starts, or the token unchanged.

        Returns the token when it is already in the vocabulary, when it is
        too short to be evidence, or when more than one index word starts
        with it — two candidates means the word is ambiguous, and picking one
        is wrong half the time.
        """
        if token in vocabulary or len(token) < cls.SHORTEST_PREFIX:
            return token
        if token in cls.STOP_AT:
            return token
        found = [word for word in vocabulary if word.startswith(token)]
        return found[0] if len(found) == 1 else token

    @classmethod
    def extend_all(cls, tokens: list[str], vocabulary: frozenset[str]) -> list[str]:
        """Extend every token, keeping the order and the count."""
        return [cls.extend(token, vocabulary) for token in tokens]
