"""Every number the scorer uses, changeable without editing the package.

The four were constants read straight out of the module, so a domain the
defaults suit badly had no recourse. One of them was worse than unreachable:
`MIN_CONTENT_OVERLAP` was exported, documented and never read — the scorer
hard-coded "any overlap at all", so a caller who raised it got no change and
no error.
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from lexmatch import Entry, Index
from lexmatch.constants import (
    DEFAULT_THRESHOLD,
    LENGTH_PENALTY,
    MIN_CONTENT_OVERLAP,
    TERM_FREQUENCY_SATURATION,
)
from lexmatch.exceptions import TuningError
from lexmatch.models.tuning import Tuning
from lexmatch.morphology import Morphology
from lexmatch.stemming import Stemmer
from lexmatch.stopwords import STOPWORDS

ENTRIES = [
    Entry(question="Are you open to remote work?", answer="Yes.", aliases=["remote"]),
    Entry(question="Can you start next month?", answer="Yes.", aliases=["availability"]),
]

# Four entries sharing one content word dilute its IDF, so BM25 stays low
# while the phrase scorer can still win on shared filler — which is where
# the overlap guard decides the outcome rather than being masked by BM25.
DILUTED = [
    Entry(question="What is your rate for design work?", answer="A.", aliases=[]),
    Entry(question="What is your rate for review work?", answer="B.", aliases=[]),
    Entry(question="What is your rate for audit work?", answer="C.", aliases=[]),
    Entry(question="What is your rate for training work?", answer="D.", aliases=[]),
]


class TestTheDefaultsChangeNothing:
    """Adopting `Tuning` has to be invisible until a caller asks otherwise."""

    def test_an_index_without_tuning_uses_the_constants(self):
        tuning = Index(ENTRIES).tuning
        assert tuning.threshold == DEFAULT_THRESHOLD
        assert tuning.saturation == TERM_FREQUENCY_SATURATION
        assert tuning.length_penalty == LENGTH_PENALTY
        assert tuning.minimum_overlap == MIN_CONTENT_OVERLAP

    def test_the_stopwords_are_the_shipped_ones(self):
        assert Index(ENTRIES).tuning.stopwords == STOPWORDS

    def test_scores_are_unchanged_by_passing_an_empty_tuning(self):
        plain = Index(ENTRIES).score("can I work remotely")
        tuned = Index(ENTRIES, tuning=Tuning()).score("can I work remotely")
        assert [value for value, _ in plain] == [value for value, _ in tuned]


class TestTheThreshold:
    # A weak but non-zero match. What counts as weak has changed twice:
    # "can I work remotely" stopped being weak when typo correction read
    # "remotely" as "remote", and "the next thing" stopped being weak when
    # BM25 gained a reachable ceiling. Weak now means a *low-IDF* word —
    # one appearing in several entries, which specificity scales down — so
    # the fixture below has "work" in all three.
    WEAK = "you work"
    WEAK_ENTRIES: ClassVar[list[Entry]] = [
        Entry(question="Are you open to remote work?", answer="Yes.", aliases=["remote"]),
        Entry(
            question="Can you start work next month?", answer="Yes.", aliases=["availability"]
        ),
        Entry(question="Do you enjoy the work?", answer="Yes.", aliases=["enjoyment"]),
    ]

    def test_raising_it_refuses_a_weak_match(self):
        entry, score = Index(self.WEAK_ENTRIES, threshold=0.9).answer(self.WEAK)
        assert 0 < score < 0.9, f"{self.WEAK!r} scored {score:.3f}, not weak"
        assert entry is None

    def test_a_low_threshold_accepts_it(self):
        entry, score = Index(self.WEAK_ENTRIES, threshold=0.1).answer(self.WEAK)
        assert score >= 0.1
        assert entry is not None

    def test_above_one_refuses_everything(self):
        """Scores cap at 1.0, so this is the honest way to turn answering
        off without taking the index apart."""
        assert Index(ENTRIES, threshold=1.01).answer("remote")[0] is None

    def test_an_explicit_threshold_wins_over_the_tuning(self):
        """A caller who named it meant it."""
        index = Index(self.WEAK_ENTRIES, threshold=0.9, tuning=Tuning(threshold=0.1))
        assert index.threshold == 0.9
        assert index.answer(self.WEAK)[0] is None

    def test_a_negative_threshold_is_refused(self):
        with pytest.raises(TuningError, match="cannot be negative"):
            Tuning(threshold=-0.1)


class TestTheOverlapGuardIsNowRead:
    """It was exported, documented and dead."""

    def test_raising_it_turns_a_confident_match_into_a_refusal(self):
        query = "what is your rate for consulting"
        # 0.446 with the guard at 1, which is a hair under the 0.45 default
        # now that phrase overlap is IDF-weighted. The threshold is lowered
        # so this test turns on the guard rather than on the threshold.
        # 0.139 with the guard at 1 and 0.084 at 2, both low because every
        # word these entries share is in all of them. The threshold is set
        # between the two so the guard is what decides.
        loose = Index(DILUTED, tuning=Tuning(minimum_overlap=1), threshold=0.1)
        strict = Index(DILUTED, tuning=Tuning(minimum_overlap=2), threshold=0.1)
        assert loose.answer(query)[0] is not None
        assert strict.answer(query)[0] is None

    def test_it_changes_the_phrase_score_directly(self):
        """Where the guard lives. Through `score()` it is often masked by
        BM25 winning the maximum, which is why the unit is checked too."""
        entries = [
            Entry(
                question="What is your notice period and start date?",
                answer="One month.",
                aliases=[],
            )
        ]
        loose = Index(entries, tuning=Tuning(minimum_overlap=1))
        strict = Index(entries, tuning=Tuning(minimum_overlap=2))
        # `score` prepares these once per query; the unit takes them ready
        # so the guard can be exercised without the whole pass.
        # Stemmed by hand, because the index stems what it holds and these
        # are being handed straight to the scorer: "notice" is "notic" there.
        # One shared content word, which is what the guard counts. "start"
        # would share a second and make both settings pass.
        asked = set(Stemmer.stem_all(["notice", "of", "termination"]))
        # The folded stopword set, because the tokens above are folded too.
        content = asked - loose._stopwords
        assert loose._phrase_score(0, asked, content, asked) > 0
        assert strict._phrase_score(0, asked, content, asked) == 0

    def test_zero_lets_a_query_match_on_filler(self):
        index = Index(DILUTED, tuning=Tuning(minimum_overlap=0))
        assert index.score("what is your")[0][0] > 0

    def test_a_negative_overlap_is_refused(self):
        with pytest.raises(TuningError, match="cannot be negative"):
            Tuning(minimum_overlap=-1)


class TestSaturationAndLengthPenalty:
    def test_saturation_changes_the_scores(self):
        low = Index(ENTRIES, tuning=Tuning(saturation=0.5))
        high = Index(ENTRIES, tuning=Tuning(saturation=4.0))
        assert low.score("remote work")[0][0] != high.score("remote work")[0][0]

    def test_zero_saturation_is_refused(self):
        """It divides by zero in the term-frequency term."""
        with pytest.raises(TuningError, match="above 0"):
            Tuning(saturation=0)

    def test_a_length_penalty_of_zero_ignores_entry_length(self):
        """Two entries differing only in length should then score alike."""
        entries = [
            Entry(question="remote work", answer="A.", aliases=[]),
            Entry(
                question="remote work and also several other unrelated topics here",
                answer="B.",
                aliases=[],
            ),
        ]
        ignored = Index(entries, tuning=Tuning(length_penalty=0.0))
        applied = Index(entries, tuning=Tuning(length_penalty=1.0))
        gap_ignored = abs(ignored.score("remote")[0][0] - ignored.score("remote")[1][0])
        gap_applied = abs(applied.score("remote")[0][0] - applied.score("remote")[1][0])
        assert gap_ignored <= gap_applied

    @pytest.mark.parametrize("value", [-0.1, 1.1, 2.0])
    def test_a_length_penalty_outside_zero_to_one_is_refused(self, value):
        with pytest.raises(TuningError, match="between 0 and 1"):
            Tuning(length_penalty=value)


class TestTheStopwordList:
    def test_extra_words_are_added(self):
        tuning = Tuning().with_stopwords(extra=["please", "kindly"])
        assert "please" in tuning.stopwords
        assert "kindly" in tuning.stopwords

    def test_the_shipped_words_are_kept_when_adding(self):
        tuning = Tuning().with_stopwords(extra=["please"])
        assert "what" in tuning.stopwords

    def test_a_word_can_be_taken_out(self):
        """For a domain where a stopword is content: "can" is also a tin,
        "will" is also a legal document."""
        assert "can" in Tuning().stopwords
        assert "can" not in Tuning().with_stopwords(keep=["can"]).stopwords

    def test_the_list_can_be_replaced_outright(self):
        """For another language."""
        tuning = Tuning().with_stopwords(["el", "la", "de"])
        assert tuning.stopwords == frozenset({"el", "la", "de"})
        assert "what" not in tuning.stopwords

    def test_keep_wins_over_extra(self):
        """Asking to keep a word is the more specific instruction."""
        tuning = Tuning().with_stopwords(extra=["rate"], keep=["rate"])
        assert "rate" not in tuning.stopwords

    def test_words_are_lower_cased(self):
        """Matching happens on normalized tokens, so a capitalized entry
        would look like it worked while matching nothing."""
        assert "please" in Tuning().with_stopwords(extra=["PLEASE"]).stopwords

    def test_the_scorer_uses_the_tuning_list(self):
        index = Index(ENTRIES, tuning=Tuning().with_stopwords(["xyzzy"]))
        assert index.tuning.stopwords == frozenset({"xyzzy"})
        assert "what" not in index.tuning.stopwords


class TestDescribe:
    def test_it_names_every_number(self):
        described = Tuning().describe()
        for part in ("threshold", "saturation", "length penalty", "minimum overlap"):
            assert part in described

    def test_it_counts_the_stopwords(self):
        described = Tuning().with_stopwords(["a", "b"]).describe()
        assert "2 stopwords" in described

    def test_it_does_not_list_them(self):
        """Safe to log: seventy-seven words in a log line is noise."""
        assert "what" not in Tuning().describe()


class TestTheUnknownWordCost:
    """Off by default, and measured twice before it was left off.

    An unknown word has no inverse document frequency, so it contributes
    nothing to the score ceiling and is invisible — which leaves a query
    satisfiable by matching only the words it happened to share. Charging
    for it nonetheless made the library worse across 133 measured questions,
    because in a question set small enough to hand write, most words in a
    naturally phrased question are absent from every entry.
    """

    SPARSE: ClassVar[list[Entry]] = [
        Entry(question="Are you open to remote work?", answer="REMOTE", aliases=["remote"]),
        Entry(question="What is your notice period?", answer="NOTICE", aliases=["notice"]),
        Entry(question="What are your rates?", answer="RATE", aliases=["rate"]),
    ]
    #: One known content word, one the index has never seen.
    HALF_KNOWN = "do you like working alone"

    def test_it_is_off_by_default(self):
        assert Tuning().unknown_word_cost == 0.0

    def test_off_the_query_is_answered_on_its_known_word(self):
        """The documented cost of leaving it off."""
        assert Index(self.SPARSE).reply(self.HALF_KNOWN).answered

    def test_raising_it_lowers_the_score(self):
        loose = Index(self.SPARSE)
        strict = Index(self.SPARSE, tuning=Tuning(unknown_word_cost=1.0))
        assert strict.score(self.HALF_KNOWN)[0][0] < loose.score(self.HALF_KNOWN)[0][0]

    def test_a_fully_recognized_query_is_unaffected(self):
        loose = Index(self.SPARSE)
        strict = Index(self.SPARSE, tuning=Tuning(unknown_word_cost=1.0))
        for query in ("remote work", "notice period", "rate"):
            assert strict.score(query)[0][0] == loose.score(query)[0][0], query

    def test_a_cost_outside_zero_to_one_is_refused(self):
        with pytest.raises(TuningError, match="between 0 and 1"):
            Tuning(unknown_word_cost=1.5)


class TestTheStemmerIsReplaceable:
    FORMS: ClassVar[list[Entry]] = [
        Entry(question="Do you do consulting?", answer="CONSULTING", aliases=["consulting"]),
        Entry(question="What is your notice period?", answer="NOTICE", aliases=["notice"]),
    ]

    def test_it_is_on_by_default(self):
        """So "do you consult" reaches the consulting entry."""
        assert Index(self.FORMS).reply("do you consult").entry.answer == "CONSULTING"

    def test_none_matches_exact_word_forms_only(self):
        """Both have to be off. Turning off the stemmer alone leaves
        `Morphology`, which bridges "consult" to "consulting" by prefix —
        a different mechanism reaching the same pair."""
        exact = Index(
            self.FORMS,
            tuning=Tuning().with_stemmer(None).with_morphology(None),
        )
        assert not exact.reply("do you consult").answered
        assert exact.reply("consulting").answered

    def test_morphology_alone_also_bridges_it(self):
        """So the test above is turning off two things for a reason."""
        stemless = Index(self.FORMS, tuning=Tuning().with_stemmer(None))
        assert stemless.reply("do you consult").answered

    def test_a_replacement_is_used(self):
        """Any callable from a word to a token, so a Snowball stemmer or a
        lemmatizer drops in."""
        shouty = Index(self.FORMS, tuning=Tuning().with_stemmer(str.upper))
        assert shouty.reply("CONSULTING").answered

    def test_describe_says_which(self):
        assert "stemming on" in Tuning().describe()
        assert "stemming off" in Tuning().with_stemmer(None).describe()


class TestMorphologyIsReplaceable:
    """A query word may be the start of a longer word the index holds.

    Stemming folds inflection and deliberately stops at derivation, because
    the endings it would have to strip change what a word means. An index
    holding "seniority" and not "senior" is then unreachable by "are you a
    senior", and nothing reports it.
    """

    DERIVED: ClassVar[list[Entry]] = [
        Entry(
            question="How many years of experience?",
            answer="YEARS",
            aliases=["seniority", "experience"],
        ),
        Entry(
            question="How do you think about security?", answer="SECURITY", aliases=["security"]
        ),
        Entry(question="What is your notice period?", answer="NOTICE", aliases=["notice"]),
    ]

    def test_it_is_on_by_default(self):
        assert Index(self.DERIVED).reply("are you a senior").entry.answer == "YEARS"

    def test_it_works_in_stem_space(self):
        """ "secure" folds to "secur", which is a prefix of "security"; the
        unfolded "secure" is a prefix of nothing because of its "e"."""
        assert Index(self.DERIVED).reply("is it secure").entry.answer == "SECURITY"

    def test_none_turns_it_off(self):
        off = Index(self.DERIVED, tuning=Tuning().with_morphology(None))
        assert not off.reply("are you a senior").answered

    def test_an_ambiguous_prefix_is_left_alone(self):
        """Two index words starting the same way means the query word is
        ambiguous, and picking one is wrong half the time."""
        both = [
            Entry(question="How do you design a system?", answer="DESIGN", aliases=["design"]),
            Entry(
                question="How do you work with a designer?",
                answer="DESIGNER",
                aliases=["designer"],
            ),
        ]
        index = Index(both)
        assert Morphology.extend("design", index._stemmed_vocabulary) == "design"

    def test_a_short_word_is_not_evidence(self):
        vocabulary = frozenset({"leadership", "planet"})
        assert Morphology.extend("plan", vocabulary) == "plan"

    def test_it_only_ever_lengthens_toward_a_word_the_index_holds(self):
        """It cannot invent a term."""
        assert Morphology.extend("senior", frozenset({"notice"})) == "senior"

    def test_a_complete_word_is_protected(self):
        assert Morphology.extend("there", frozenset({"therefore"})) == "there"

    def test_describe_says_which(self):
        assert "morphology on" in Tuning().describe()
        assert "morphology off" in Tuning().with_morphology(None).describe()

    def test_a_replacement_is_used(self):
        shouty = Index(
            self.DERIVED,
            tuning=Tuning().with_morphology(lambda words, vocab: [w.upper() for w in words]),
        )
        assert shouty.reply("notice") is not None
