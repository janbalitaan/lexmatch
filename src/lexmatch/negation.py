"""Spotting a question asked in the negative."""

from __future__ import annotations

import re


class Negation:
    """Detects whether a question is asking the opposite.

    Lexical matching cannot tell a question from its negation, because they
    share every substantive word. "Are you *not* open to remote work" scored
    0.923 against the affirmative entry and would have been answered "Yes" —
    the opposite of correct, said confidently.

    The words that carry the negation are stopwords, so they are stripped
    before scoring ever sees them. Which means this has to look at the raw
    text, before normalization, and it has to run separately rather than as
    a scoring adjustment.

    Detection, not resolution. Knowing a question is negative does not say
    what the answer is — "are you not available" might be answered "no, I
    am available", and getting that right needs the meaning of the entry,
    not its words. So the reply is marked and the caller decides.
    """

    # The negations that invert a question rather than appearing inside a
    # phrase. `\b` on both sides, because "cannot" contains "can" and
    # "nothing" contains "not".
    _NEGATIONS = re.compile(
        r"\b(?:not|never|isn'?t|aren'?t|wasn'?t|weren'?t|don'?t|doesn'?t|"
        r"didn'?t|won'?t|wouldn'?t|can'?t|cannot|couldn'?t|shouldn'?t|"
        r"haven'?t|hasn'?t|hadn'?t|no longer|neither|nor)\b",
        re.IGNORECASE,
    )

    @classmethod
    def present_in(cls, text: str) -> bool:
        """Whether this text asks something in the negative."""
        return bool(cls._NEGATIONS.search(text))

    @classmethod
    def disagree(cls, query: str, question: str) -> bool:
        """Whether one of these is negative and the other is not.

        Both negative is agreement: "aren't you remote" against "aren't you
        in the office" are both negative questions and the match is as good
        as any other. It is the mismatch that inverts the answer.
        """
        return cls.present_in(query) != cls.present_in(question)
