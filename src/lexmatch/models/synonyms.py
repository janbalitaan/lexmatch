"""Words that should count as the same word."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from lexmatch.exceptions import SynonymError


@dataclass(frozen=True)
class Synonyms:
    """A map from a word to the words it should be read as.

    Aliases solve this per entry, which is right when a phrasing belongs to
    one question. It is wrong when a word means the same thing everywhere:
    writing `wfh` into the aliases of every entry that mentions remote work
    is the same fact recorded five times, and the fifth entry is the one
    somebody forgets.

    A synonym is declared once and applies to the whole index:

        Synonyms.of({
            "wfh": "work from home",
            "comp": "compensation",
            "ooo": "out of office",
        })

    Expansion is **one-directional and additive**. A query token that has an
    entry is replaced by its expansion; a token with no entry is left alone.
    Both the entries and the queries go through the same map, so the two
    sides meet in the middle whichever one used the short form.

    Additive rather than substitutive for the ambiguous cases: `expand`
    keeps the original token alongside its expansion, so `comp` still matches
    an entry that literally says "comp" as well as one saying
    "compensation". Dropping the original would trade one miss for another.
    """

    mapping: Mapping[str, tuple[str, ...]] = field(default_factory=lambda: MappingProxyType({}))

    @property
    def longest_key(self) -> int:
        """Return how many tokens the longest key spans.

        Bounds the lookahead when scanning: a map of single words needs a
        window of one, and a map holding "how much" needs two.
        """
        return max((len(key.split()) for key in self.mapping), default=1)

    @classmethod
    def of(cls, pairs: Mapping[str, str | Iterable[str]]) -> Synonyms:
        """Build from a plain dict, accepting a phrase or a list of words.

        `{"wfh": "work from home"}` and `{"wfh": ["work", "from", "home"]}`
        mean the same thing; the first is what anyone would write.

        Keys may be phrases. `{"how much": "rate"}` is the point — a
        paraphrase that shares no word with the question is the one thing
        neither stopwords nor single-word synonyms can bridge, and "how much
        do you charge" against "what is your rate" is the ordinary case.

        An earlier version refused a multi-word key on the grounds that
        expansion happened one token at a time. That was a statement about
        the implementation rather than a constraint, and the implementation
        changed.

        Keys are lower-cased, because matching happens on normalized tokens
        and a capitalized key would look like it worked while matching
        nothing.
        """
        built: dict[str, tuple[str, ...]] = {}
        for word, expansion in pairs.items():
            key = word.strip().lower()
            if not key:
                raise SynonymError("a synonym key cannot be empty")
            words = expansion.split() if isinstance(expansion, str) else list(expansion)
            terms = tuple(term.strip().lower() for term in words if term.strip())
            if not terms:
                raise SynonymError(
                    f"the synonym {word!r} expands to nothing; remove it or give it a value"
                )
            built[key] = terms
        return cls(mapping=MappingProxyType(built))

    def expand(self, tokens: Iterable[str]) -> list[str]:
        """Return the tokens with every known synonym expanded in place.

        Phrases are matched **longest first**, so a map holding both
        `"how much"` and `"much"` reads "how much" as the phrase rather than
        stopping at the shorter key. Without that the longer entry could
        never fire, which is the same silent failure as refusing it outright.

        The original tokens are kept alongside the expansion, so a short form
        still matches an entry that uses the short form.
        """
        if not self.mapping:
            return list(tokens)
        words = list(tokens)
        longest = self.longest_key
        expanded: list[str] = []
        position = 0
        while position < len(words):
            span, terms = self._match_at(words, position, longest)
            expanded.extend(words[position : position + span])
            expanded.extend(terms)
            position += span
        return expanded

    def _match_at(
        self, words: list[str], position: int, longest: int
    ) -> tuple[int, tuple[str, ...]]:
        """Return how many tokens matched here, and what they expand to.

        A span of 1 with no terms means nothing matched and the token passes
        through — so the caller advances by one either way and the scan
        cannot stall.
        """
        for span in range(min(longest, len(words) - position), 0, -1):
            phrase = " ".join(words[position : position + span])
            terms = self.mapping.get(phrase)
            if terms is not None:
                return span, terms
        return 1, ()

    def with_pairs(self, pairs: Mapping[str, str | Iterable[str]]) -> Synonyms:
        """Return these synonyms plus more, the later ones winning."""
        merged: dict[str, str | Iterable[str]] = {
            word: list(terms) for word, terms in self.mapping.items()
        }
        merged.update(pairs)
        return Synonyms.of(merged)

    def describe(self) -> str:
        """Summarize, for a line that is safe to log."""
        return f"{len(self.mapping)} synonyms"
