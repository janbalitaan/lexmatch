"""Folding a word's inflections onto one token.

Without this, *"consulting"* and *"consult"* are unrelated tokens, and a
query using one cannot reach an entry using the other. For a question set
you write yourself that is fixable with an alias, and for a long time this
library said so. It stops being fixable at the scale a support or
documentation index runs at: nobody hand-writes aliases for every tense and
plural across four hundred entries, and the ones they forget are invisible
until somebody is not answered.

What this is **not** is a Porter stemmer. Porter strips derivational
suffixes too, which merges words that mean different things — "university"
and "universe" both become "univers", and an index about one will answer
questions about the other. That is a bad trade for a bot whose job includes
refusing what it does not know.

So only inflection is folded, the endings that mark number and tense without
changing what a word is about:

    plural      rates, taxes, policies      ->  rate, tax, policy
    verb        consulting, consulted        ->  consult
    adverb      remotely, quickly            ->  remote, quick

Derivational endings are left alone. "payment" stays distinct from "pay" and
"consultant" from "consult", because the difference between them is usually
the difference between two entries.
"""

from __future__ import annotations

from functools import lru_cache
from typing import ClassVar


class Stemmer:
    """Strips inflectional endings, conservatively.

    Replace `IRREGULAR` or `SUFFIXES` to change what folds, or pass a
    different callable as `Tuning.stemmer` to replace the whole approach —
    a Snowball stemmer, a lemmatizer, or nothing at all.
    """

    #: Words whose inflection is not a suffix, so no rule can reach them.
    #: These are the ones that came up in measured traffic; add your own
    #: domain's irregulars by replacing the mapping.
    IRREGULAR: ClassVar[dict[str, str]] = {
        "built": "build",
        "bought": "buy",
        "sought": "seek",
        "taught": "teach",
        "led": "lead",
        "ran": "run",
        "run": "run",
        "began": "begin",
        "begun": "begin",
        "wrote": "write",
        "written": "write",
        "spoke": "speak",
        "spoken": "speak",
        "took": "take",
        "taken": "take",
        "gave": "give",
        "given": "give",
        "made": "make",
        "paid": "pay",
        "said": "say",
        "sold": "sell",
        "told": "tell",
        "held": "hold",
        "kept": "keep",
        "left": "leave",
        "met": "meet",
        "sent": "send",
        "spent": "spend",
        "lost": "lose",
        "found": "find",
        "grew": "grow",
        "grown": "grow",
        "knew": "know",
        "known": "know",
        "saw": "see",
        "seen": "see",
        "went": "go",
        "gone": "go",
        "did": "do",
        "done": "do",
        "chose": "choose",
        "chosen": "choose",
        "drove": "drive",
        "driven": "drive",
        "rose": "rise",
        "risen": "rise",
        "people": "person",
        "children": "child",
        "men": "man",
        "women": "woman",
        "data": "datum",
        "criteria": "criterion",
        "analyses": "analysis",
        "indices": "index",
        "matrices": "matrix",
    }

    #: Words a rule would damage. "process" is not a plural of "proces", and
    #: "css" is not a plural of anything.
    #:
    #: The "-ing" entries are the ones that are solidly nouns — a question
    #: about training is not a question about trains. "building" is
    #: deliberately absent, because in the indexes this serves it is far more
    #: often the verb ("how do you build a team"); add it back for an index
    #: about premises.
    KEEP: ClassVar[frozenset[str]] = frozenset(
        {
            "as",
            "is",
            "was",
            "has",
            "his",
            "its",
            "this",
            "thus",
            "yes",
            "gas",
            "bus",
            "plus",
            "minus",
            "status",
            "focus",
            "bonus",
            "campus",
            "virus",
            "census",
            "process",
            "access",
            "success",
            "address",
            "business",
            "progress",
            "express",
            "across",
            "less",
            "class",
            "pass",
            "miss",
            "boss",
            "loss",
            "cross",
            "press",
            "stress",
            "css",
            "js",
            "aws",
            "ops",
            "devops",
            "kubernetes",
            "series",
            "species",
            "news",
            "always",
            "perhaps",
            "during",
            "string",
            "ring",
            "king",
            "thing",
            "bring",
            "spring",
            "being",
            "ceiling",
            "billing",
            "meeting",
            "training",
            "funding",
            "banking",
            "marketing",
            "engineering",
            "onboarding",
            "red",
            "bed",
            "fed",
            "led",
            "need",
            "speed",
            "feed",
            "seed",
            "exceed",
            "proceed",
            "succeed",
            "embed",
            "bond",
            "only",
            "early",
            "likely",
            "daily",
            "weekly",
            "monthly",
            "yearly",
            "family",
            "supply",
            "apply",
            "reply",
            "rely",
            "fly",
            "july",
            "italy",
            "ally",
            "rally",
            "really",
            "fully",
            "duly",
            "truly",
        }
    )

    #: Ending, replacement, and the shortest stem the rule may leave. Order
    #: matters: the first match wins, so longer endings come first.
    SUFFIXES: ClassVar[tuple[tuple[str, str, int], ...]] = (
        ("ingly", "", 4),
        ("edly", "", 4),
        ("ies", "y", 3),
        ("ied", "y", 3),
        ("ier", "y", 3),
        ("iest", "y", 3),
        ("sses", "ss", 4),
        ("shes", "sh", 4),
        ("ches", "ch", 4),
        ("xes", "x", 3),
        ("zes", "z", 3),
        ("ses", "s", 4),
        ("ing", "", 4),
        ("ed", "", 4),
        ("ly", "", 4),
        ("es", "", 4),
        ("s", "", 3),
    )

    #: A doubled consonant left by stripping "ing" or "ed" collapses, so
    #: "running" reaches "run" rather than "runn". Not for these, where the
    #: double belongs to the word.
    _KEEPS_DOUBLE: ClassVar[frozenset[str]] = frozenset({"ll", "ss", "zz", "ff"})

    #: Endings that look like a plural "s" and are not. "analysis" is not
    #: the plural of "analysi", and nor are "basis", "thesis", "crisis",
    #: "status" or "campus" — a rule covers the class, where a word list
    #: would have to name every member.
    #:
    #: Only these three, because the near misses are genuine plurals:
    #: "-ys" would block "deploys" and "ways", "-os" would block "videos"
    #: and "demos". "always" is on KEEP instead, where the exceptions that
    #: do not form a class belong.
    _NOT_PLURAL: ClassVar[tuple[str, ...]] = ("is", "us", "ss")

    _VOWELS: ClassVar[frozenset[str]] = frozenset("aeiouy")

    #: A word this short has no inflection worth stripping.
    _SHORTEST_WORD: ClassVar[int] = 4

    #: Below this a doubled consonant is part of the word, not an artifact.
    _SHORTEST_DOUBLED: ClassVar[int] = 4

    #: A trailing "e" comes off only from this length up, so "note" and
    #: "rate" keep their shape.
    _SHORTEST_FOR_E: ClassVar[int] = 5

    @classmethod
    def stem(cls, word: str) -> str:
        """Fold one word onto its stem, memoized.

        Pure, and called on every token of every entry and every query over a
        vocabulary that repeats heavily, so the cache turns almost all of
        those calls into a dict lookup. Cleared automatically when the rule
        tables are replaced through `configure`; call `forget` after setting
        them directly.

        Returns the word unchanged when no rule applies, when the word is on
        `KEEP`, or when applying a rule would leave something too short to be
        a word.
        """
        return cls._stem_cached(word)

    @classmethod
    def forget(cls) -> None:
        """Drop the memo, after the rule tables are changed in place."""
        cls._stem_cached.cache_clear()

    @classmethod
    @lru_cache(maxsize=100_000)
    def _stem_cached(cls, word: str) -> str:
        """Apply the rules. Wrapped by `stem`, which is the public name."""
        if word in cls.IRREGULAR:
            # Trimmed like any other stem. The mapping is written in whole
            # words so it reads as English, but written mapping to "write"
            # while "write" itself folds to "writ" would put an irregular
            # form and its own base on different tokens.
            return cls._trim_e(cls.IRREGULAR[word])
        if word in cls.KEEP or len(word) < cls._SHORTEST_WORD or not cls._has_vowel(word):
            return word
        for ending, replacement, shortest in cls.SUFFIXES:
            if not word.endswith(ending):
                continue
            if ending == "s" and word.endswith(cls._NOT_PLURAL):
                continue
            stem = word[: -len(ending)] + replacement
            if len(stem) < shortest or not cls._has_vowel(stem):
                continue
            stem = cls._collapse(stem) if ending in {"ing", "ed"} else stem
            return cls._trim_e(stem)
        return cls._trim_e(word)

    @classmethod
    def _trim_e(cls, word: str) -> str:
        """Drop a trailing "e" so a stem agrees with its own base word.

        Stripping "-ing" from "scaling" leaves "scal", and "-ed" from
        "managed" leaves "manag" — neither of which matches "scale" or
        "manage". Restoring the "e" needs rules that get "experienced" wrong
        whichever way they are written, so the "e" comes off *both* sides
        instead. "scale" and "scaling" both become "scal", "experience" and
        "experienced" both become "experienc".

        A stem is never shown to anyone, so it does not need to be a word.
        It needs to be the same word for every inflection, which this is.

        Only from five characters up, so "note", "rate" and "code" keep their
        shape and do not collide with "not", "rat" and "cod".
        """
        if len(word) >= cls._SHORTEST_FOR_E and word.endswith("e"):
            return word[:-1]
        return word

    @classmethod
    def stem_all(cls, words: list[str]) -> list[str]:
        """Fold every word in a list, keeping the order and the count."""
        return [cls.stem(word) for word in words]

    @classmethod
    def _collapse(cls, stem: str) -> str:
        """Undo the consonant doubling that "-ing" and "-ed" add."""
        doubled = len(stem) >= cls._SHORTEST_DOUBLED and stem[-1] == stem[-2]
        if doubled and stem[-2:] not in cls._KEEPS_DOUBLE:
            return stem[:-1]
        return stem

    @classmethod
    def _has_vowel(cls, word: str) -> bool:
        """Whether a word has a vowel, which a real stem does."""
        return any(char in cls._VOWELS for char in word)
