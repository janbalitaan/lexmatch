"""What kind of answer a query got."""

from __future__ import annotations

from enum import Enum


class Outcome(str, Enum):
    """Why a reply says what it says.

    A single score cannot carry this. "Nothing matched" and "two things
    matched equally well" both leave a caller without an answer, and the
    right thing to say is different: one is "I don't know that", the other
    is "which did you mean?". Collapsing them is how a bot comes to answer
    confidently about design rates when it was asked about rates.

    A `str` enum so it serializes into JSON as its name, which is where a
    reply usually ends up.
    """

    ANSWERED = "answered"
    """One entry won clearly. Say its answer."""

    AMBIGUOUS = "ambiguous"
    """Two or more entries scored within the margin of each other.

    Both cleared the threshold, so the question was understood — it just was
    not specific enough to pick between them. Offer the alternatives rather
    than guessing: a coin flip here is a confident wrong answer half the
    time, and the visitor has no way to tell which half they got.
    """

    UNANSWERED = "unanswered"
    """Nothing cleared the threshold. Say so, and offer the near misses."""

    NEGATED = "negated"
    """The query was negative and the matched question was not.

    "Are you *not* open to remote work" matches the affirmative entry at
    0.923 and would have been answered "Yes" — which is the opposite of
    correct. Lexical matching cannot tell a question from its negation,
    because they share every substantive word.

    Reported rather than answered, so a caller can rephrase, escalate, or
    answer carefully instead of confidently wrong.
    """
