"""Breaking a message into the questions it contains."""

from __future__ import annotations

import re


class QuestionSplitter:
    """Separates a message that asks more than one thing.

    One question scores well. Two in the same message score *worse than
    either would alone*, and the reason is arithmetic rather than a bug: the
    phrase measure is an overlap ratio, so doubling the query's length halves
    the proportion any single entry can share. Measured on a three-part
    message, the best entry fell to 0.480 and the other two to 0.400 and
    0.250 — below the threshold, so asking three things got one answer and
    two silent omissions.

    Splitting first turns that into three questions that each score 1.000.

    Conservative on purpose. A split that is wrong costs an answer to a
    question nobody asked, so only separators that reliably end a question
    are used: `and` splits before an interrogative word and not otherwise,
    so "remote and hybrid work" stays one question while "what are your
    rates and when can you start" becomes two.
    """

    # A question mark ends a question. A semicolon and a newline are the
    # written equivalents. `and`, `also` and `plus` join clauses, but only
    # when what follows looks like another question rather than the rest of
    # this one — "rates and availability" is one question about two things,
    # while "what are your rates and when can you start" is two questions.
    _TERMINATORS = re.compile(r"[?;\n]+")
    _CONJUNCTIONS = re.compile(
        r"\s+(?:and|also|plus|then)\s+(?=(?:what|when|where|who|why|how|which|do|does|did|are|is|was|can|could|will|would|should|have|has|had)\b)",
        re.IGNORECASE,
    )

    @classmethod
    def split(cls, message: str) -> list[str]:
        """Return the questions in this message, in order.

        A message with one question comes back as a single-item list, so a
        caller never needs to special-case the common shape.
        """
        parts: list[str] = []
        for sentence in cls._TERMINATORS.split(message):
            parts.extend(cls._CONJUNCTIONS.split(sentence))
        return cls._keep_usable(parts)

    @classmethod
    def looks_compound(cls, message: str) -> bool:
        """Whether this message asks more than one thing."""
        return len(cls.split(message)) > 1

    @classmethod
    def _keep_usable(cls, parts: list[str]) -> list[str]:
        """Drop the empty fragments that splitting leaves behind.

        Short ones are kept. An earlier version folded any single word into
        its neighbour, on the theory that one word cannot carry a question —
        and "remote? rates? notice period?" came back as two questions, the
        first of them "remote rates", which means neither. A word before a
        question mark is a question; the terminator already said so.
        """
        return [part.strip() for part in parts if part.strip()]
