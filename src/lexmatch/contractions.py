"""Reading a contraction as the words it stands for.

Normalizing drops the apostrophe, so "don't" arrives as `dont` — a token in
no stopword list and in no entry, which the weighting therefore treats as one
of the most discriminating words in the index. Measured against a
twenty-five entry index, `youv` (from "you've") scored 3.06, the same as the
rarest real term there.

Informal writing is full of them, and informal writing is most of what a
question box receives. So each one is replaced by the words it stands for,
and those words are ordinary stopwords:

    dont   -> do not
    youve  -> you have
    whats  -> what is

Expanding rather than listing the contracted forms as stopwords, because the
words are sometimes wanted: "what is your rate" needs its "what is" for
phrase scoring, and "I don't need sponsorship" needs its "not" for negation
to see.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import ClassVar


class Contractions:
    """Expands contracted forms, with the apostrophe already gone.

    Replace `FORMS` to add to them, or to drop one whose expansion is wrong
    for a particular corpus.
    """

    #: Keyed on the apostrophe-stripped form, because that is what reaches
    #: this after normalization — which also means "dont" and "don't" are
    #: handled by one entry.
    #:
    #: Ambiguous forms are deliberately absent, because expanding them is
    #: wrong as often as it is right: "ill" is a word, and so are "well",
    #: "id", "wed", "shed" and "lets". "its", "were", "hes" and "shes" are
    #: left alone for the same reason, and the first two are stopwords
    #: already.
    FORMS: ClassVar[Mapping[str, tuple[str, ...]]] = MappingProxyType(
        {
            "im": ("i", "am"),
            "ive": ("i", "have"),
            "youve": ("you", "have"),
            "weve": ("we", "have"),
            "theyve": ("they", "have"),
            "youre": ("you", "are"),
            "theyre": ("they", "are"),
            "whats": ("what", "is"),
            "thats": ("that", "is"),
            "hows": ("how", "is"),
            "wheres": ("where", "is"),
            "theres": ("there", "is"),
            "whos": ("who", "is"),
            "whens": ("when", "is"),
            "whys": ("why", "is"),
            "youd": ("you", "would"),
            "youll": ("you", "will"),
            "theyll": ("they", "will"),
            "dont": ("do", "not"),
            "doesnt": ("does", "not"),
            "didnt": ("did", "not"),
            "cant": ("can", "not"),
            "cannot": ("can", "not"),
            "couldnt": ("could", "not"),
            "wouldnt": ("would", "not"),
            "shouldnt": ("should", "not"),
            "wont": ("will", "not"),
            "isnt": ("is", "not"),
            "arent": ("are", "not"),
            "wasnt": ("was", "not"),
            "werent": ("were", "not"),
            "havent": ("have", "not"),
            "hasnt": ("has", "not"),
            "hadnt": ("had", "not"),
            "aint": ("is", "not"),
            "gonna": ("going", "to"),
            "wanna": ("want", "to"),
            "gotta": ("got", "to"),
        }
    )

    @classmethod
    def expand(cls, words: list[str]) -> list[str]:
        """Replace each contraction with its words, keeping the order."""
        expanded: list[str] = []
        for word in words:
            expanded.extend(cls.FORMS.get(word, (word,)))
        return expanded

    @classmethod
    def holds(cls, word: str) -> bool:
        """Whether this word is a contraction this knows how to expand."""
        return word in cls.FORMS
