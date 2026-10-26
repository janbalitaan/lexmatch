"""The numbers that decide what counts as a match."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field, replace

from lexmatch.constants import (
    AMBIGUITY_FLOOR,
    AMBIGUITY_MARGIN,
    DEFAULT_THRESHOLD,
    LENGTH_PENALTY,
    MIN_CONTENT_OVERLAP,
    TERM_FREQUENCY_SATURATION,
    UNKNOWN_WORD_COST,
)
from lexmatch.exceptions import TuningError
from lexmatch.models.corrections import Corrections
from lexmatch.models.synonyms import Synonyms
from lexmatch.morphology import Morphology
from lexmatch.stemming import Stemmer
from lexmatch.stopwords import STOPWORDS


@dataclass(frozen=True)
class Tuning:
    """How an index scores, as data a caller can change.

    These were constants read straight out of the module, so changing one
    meant editing the installed package. The defaults suit a question set of
    the size most people have — a few dozen entries of a sentence or two —
    and the realistic reasons to move them are immediate: entries that are
    paragraphs rather than questions, a domain whose vocabulary the stopword
    list eats, a bot that should answer more readily or less.

    Frozen, and every adjustment returns a new set, so an index cannot have
    its scoring changed underneath it after it was built.

        Tuning().with_threshold(0.6)            # answer less readily
        Tuning().with_stopwords(extra=["please"])
        Tuning(length_penalty=0.0)              # entry length stops mattering
    """

    threshold: float = DEFAULT_THRESHOLD
    saturation: float = TERM_FREQUENCY_SATURATION
    length_penalty: float = LENGTH_PENALTY
    minimum_overlap: int = MIN_CONTENT_OVERLAP
    ambiguity_margin: float = AMBIGUITY_MARGIN
    ambiguity_floor: float = AMBIGUITY_FLOOR
    unknown_word_cost: float = UNKNOWN_WORD_COST
    stemmer: Callable[[str], str] | None = Stemmer.stem
    morphology: Callable[[list[str], frozenset[str]], list[str]] | None = Morphology.extend_all
    stopwords: frozenset[str] = STOPWORDS
    synonyms: Synonyms = field(default_factory=Synonyms)
    corrections: Corrections = field(default_factory=Corrections)

    def __post_init__(self) -> None:
        """Reject a configuration that could not score anything sensibly."""
        if self.threshold < 0.0:
            raise TuningError(
                f"threshold cannot be negative (got {self.threshold}); 0 "
                "answers on any non-zero score, which is already the loosest "
                "setting that means anything"
            )
        if self.saturation <= 0:
            raise TuningError(
                f"saturation has to be above 0 (got {self.saturation}); at 0 "
                "the term-frequency term divides by zero"
            )
        if not 0.0 <= self.length_penalty <= 1.0:
            raise TuningError(
                f"length_penalty has to be between 0 and 1 (got "
                f"{self.length_penalty}); 0 ignores entry length entirely and "
                "1 applies it in full"
            )
        if self.ambiguity_margin < 0:
            raise TuningError(
                f"ambiguity_margin cannot be negative (got "
                f"{self.ambiguity_margin}); 0 means only an exact tie counts "
                "as ambiguous"
            )
        if not 0.0 <= self.unknown_word_cost <= 1.0:
            raise TuningError(
                f"unknown_word_cost has to be between 0 and 1 (got "
                f"{self.unknown_word_cost}); it scales a normalized score"
            )
        if not 0.0 <= self.ambiguity_floor <= 1.0:
            raise TuningError(
                f"ambiguity_floor has to be between 0 and 1 (got "
                f"{self.ambiguity_floor}); it is compared against a normalized "
                "score"
            )
        if self.minimum_overlap < 0:
            raise TuningError(
                f"minimum_overlap cannot be negative (got {self.minimum_overlap}); "
                "0 lets a query match on stopwords alone"
            )

    def fold(self, words: list[str]) -> list[str]:
        """Apply the stemmer, or return the words untouched without one.

        Called on both the index and the query, so the two always agree. A
        stem is never displayed, so it does not have to be a word — it has to
        be the same for every inflection, which is what `Stemmer` provides.
        """
        if self.stemmer is None:
            return words
        return [self.stemmer(word) for word in words]

    def with_morphology(
        self, morphology: Callable[[list[str], frozenset[str]], list[str]] | None
    ) -> Tuning:
        """Replace the derivational bridge, or pass None to turn it off.

        Tuning().with_morphology(None)   # exact stems only
        """
        return replace(self, morphology=morphology)

    def with_stemmer(self, stemmer: Callable[[str], str] | None) -> Tuning:
        """Replace the stemmer, or pass None to match exact word forms only.

        Tuning().with_stemmer(None)                 # no folding
        Tuning().with_stemmer(SnowballStemmer().stem)
        """
        return replace(self, stemmer=stemmer)

    def with_threshold(self, threshold: float) -> Tuning:
        """Return tuning that answers more or less readily.

        Raise it when a wrong answer costs more than no answer — which is
        usually. Lower it when the index is small and the questions are
        worded unpredictably, and expect to write aliases instead before
        going far below the default.

        Scores are capped at 1.0, so anything **above** 1.0 refuses
        everything. That is deliberately allowed rather than rejected: it is
        the honest way to turn answering off without taking the index apart,
        and a test that wants "never match" should not have to reach for a
        mock.
        """
        return replace(self, threshold=threshold)

    def with_stopwords(
        self,
        stopwords: Iterable[str] | None = None,
        *,
        extra: Iterable[str] | None = None,
        keep: Iterable[str] | None = None,
    ) -> Tuning:
        """Return tuning with a different stopword list.

        Three ways, because three different things go wrong:

        `extra` adds words that carry no signal in one domain — "please",
        "kindly", a product name in every entry. A term in every entry
        already scores zero through IDF, so this is for the ones that are
        merely frequent.

        `keep` removes words from the list, for a domain where a stopword is
        content. "can" is a stopword and a tin; "will" is a stopword and a
        legal document. Those queries score zero until the word is kept.

        `stopwords` replaces the list outright, for another language.

        Applied in that order, so `extra` and `keep` act on whatever
        `stopwords` set — and a word in both is kept, because asking to keep
        a word is the more specific instruction.
        """
        chosen = STOPWORDS if stopwords is None else frozenset(stopwords)
        chosen |= frozenset(word.lower() for word in (extra or ()))
        chosen -= frozenset(word.lower() for word in (keep or ()))
        return replace(self, stopwords=chosen)

    def with_synonyms(self, pairs: Mapping[str, str | Iterable[str]]) -> Tuning:
        """Return tuning that reads these words as each other.

        For a word that means the same thing across the whole index, where an
        alias per entry would be the same fact recorded five times:

            Tuning().with_synonyms({"wfh": "work from home"})

        Added to whatever synonyms are already set, the new ones winning on a
        repeated key. See `lexmatch.models.synonyms`.
        """
        return replace(self, synonyms=self.synonyms.with_pairs(pairs))

    def with_corrections(
        self,
        *,
        enabled: bool = True,
        similarity: float | None = None,
        minimum_length: int | None = None,
    ) -> Tuning:
        """Return tuning that reads mistyped words as the words they are.

        On by default. `enabled=False` turns it off for an index whose
        vocabulary is deliberately close together — product codes, part
        numbers — where every token is one edit from another and correcting
        is guessing.

        Raise `similarity` toward 1.0 to correct less, lower it to correct
        more. See `lexmatch.models.corrections`.
        """
        current = self.corrections
        return replace(
            self,
            corrections=Corrections(
                similarity=current.similarity if similarity is None else similarity,
                minimum_length=(
                    current.minimum_length if minimum_length is None else minimum_length
                ),
                enabled=enabled,
            ),
        )

    def describe(self) -> str:
        """Summarize the tuning, for a line that is safe to log."""
        return (
            f"threshold {self.threshold}, saturation {self.saturation}, "
            f"length penalty {self.length_penalty}, "
            f"minimum overlap {self.minimum_overlap}, "
            f"ambiguity margin {self.ambiguity_margin}, "
            f"ambiguity floor {self.ambiguity_floor}, "
            f"unknown word cost {self.unknown_word_cost}, "
            f"{'stemming on' if self.stemmer else 'stemming off'}, "
            f"{'morphology on' if self.morphology else 'morphology off'}, "
            f"{len(self.stopwords)} stopwords, {self.synonyms.describe()}, "
            f"{self.corrections.describe()}"
        )
