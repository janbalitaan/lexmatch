"""The cheap gate in typo correction must not change a single answer.

`Corrections._best` skips the real comparison when a shared-character bound
says no candidate can clear the threshold. The bound is what
`SequenceMatcher.quick_ratio` computes, and it is a true upper bound on
`ratio`, so skipping on it cannot lose a match.

That is an argument, not a guarantee. This holds the argument to account by
comparing against an ungated reference over every probe it can think of: the
vocabulary itself, single-edit typos of it, and random noise.
"""

from __future__ import annotations

from difflib import SequenceMatcher
import random
import string

import pytest

from lexmatch.models.corrections import Corrections

WORDS = (
    "notice",
    "period",
    "remote",
    "work",
    "rate",
    "salary",
    "seniority",
    "experience",
    "security",
    "testing",
    "deployment",
    "monitoring",
    "agile",
    "leadership",
    "hiring",
    "feedback",
    "estimate",
    "product",
    "scale",
    "throughput",
    "consulting",
    "advisory",
    "visa",
    "sponsorship",
)
VOCABULARY = frozenset(WORDS)


def ungated(token: str, vocabulary: frozenset[str], corrections: Corrections) -> str:
    """What `_best` did before the bound was added.

    Kept deliberately: an optimization that claims to change nothing needs
    the thing it claims to match, not a recollection of it.
    """
    if token in vocabulary or len(token) < corrections.minimum_length:
        return token
    spread = max(1, len(token) // 3)
    best: list[str] = []
    highest = corrections.similarity
    for candidate in vocabulary:
        if abs(len(candidate) - len(token)) > spread:
            continue
        ratio = SequenceMatcher(None, token, candidate).ratio()
        if ratio > highest:
            highest, best = ratio, [candidate]
        elif ratio == highest and candidate not in best:
            best.append(candidate)
    return best[0] if len(best) == 1 else token


def single_edits(seed: int = 11, per_word: int = 12) -> list[str]:
    """One typo per probe, of each kind somebody actually makes."""
    random.seed(seed)
    probes: list[str] = []
    for word in WORDS:
        for _ in range(per_word):
            chars = list(word)
            index = random.randrange(len(chars))
            action = random.choice(("swap", "drop", "insert", "replace"))
            if action == "swap" and index + 1 < len(chars):
                chars[index], chars[index + 1] = chars[index + 1], chars[index]
            elif action == "drop":
                chars.pop(index)
            elif action == "insert":
                chars.insert(index, random.choice(string.ascii_lowercase))
            else:
                chars[index] = random.choice(string.ascii_lowercase)
            probes.append("".join(chars))
    return probes


def noise(seed: int = 12, count: int = 2000) -> list[str]:
    random.seed(seed)
    return [
        "".join(random.choices(string.ascii_lowercase, k=random.randint(2, 14)))
        for _ in range(count)
    ]


class TestTheGateChangesNothing:
    @pytest.fixture
    def corrections(self) -> Corrections:
        return Corrections()

    def test_the_vocabulary_itself_is_untouched(self, corrections):
        for word in WORDS:
            assert corrections._best(word, VOCABULARY) == word

    def test_single_edit_typos_agree_with_the_reference(self, corrections):
        probes = single_edits()
        for probe in probes:
            assert corrections._best(probe, VOCABULARY) == ungated(
                probe, VOCABULARY, corrections
            ), probe

    def test_random_strings_agree_with_the_reference(self, corrections):
        for probe in noise():
            assert corrections._best(probe, VOCABULARY) == ungated(
                probe, VOCABULARY, corrections
            ), probe

    def test_it_is_actually_correcting_things(self, corrections):
        """So the agreement above is not two functions both doing nothing."""
        probes = single_edits()
        corrected = sum(1 for p in probes if corrections._best(p, VOCABULARY) != p)
        assert corrected > 50, f"only {corrected} of {len(probes)} corrected"

    @pytest.mark.parametrize("similarity", [0.6, 0.7, 0.8, 0.9])
    def test_it_holds_at_other_thresholds(self, similarity):
        """The bound is compared against the running best, so a different
        threshold exercises a different amount of skipping."""
        corrections = Corrections(similarity=similarity)
        for probe in single_edits(seed=13, per_word=4):
            assert corrections._best(probe, VOCABULARY) == ungated(
                probe, VOCABULARY, corrections
            ), f"{probe} at {similarity}"
