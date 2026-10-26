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

    @classmethod
    def of(cls, pairs: Mapping[str, str | Iterable[str]]) -> Synonyms:
        """Build from a plain dict, accepting a phrase or a list of words.

        `{"wfh": "work from home"}` and `{"wfh": ["work", "from", "home"]}`
        mean the same thing; the first is what anyone would write.

        Keys are lower-cased, because matching happens on normalized tokens
        and a capitalized key would look like it worked while matching
        nothing. A key of more than one word raises: expansion happens
        token by token, so a multi-word *key* could never match and silently
        doing nothing is worse than saying so.
        """
        built: dict[str, tuple[str, ...]] = {}
        for word, expansion in pairs.items():
            key = word.strip().lower()
            if not key:
                raise SynonymError("a synonym key cannot be empty")
            if len(key.split()) > 1:
                raise SynonymError(
                    f"the synonym key {word!r} is more than one word. Expansion "
                    "happens one token at a time, so a multi-word key can never "
                    "match — put the phrase in the entry's aliases instead."
                )
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

        The original token is kept alongside its expansion, so a short form
        still matches an entry that uses the short form.
        """
        if not self.mapping:
            return list(tokens)
        expanded: list[str] = []
        for token in tokens:
            expanded.append(token)
            expanded.extend(self.mapping.get(token, ()))
        return expanded

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
