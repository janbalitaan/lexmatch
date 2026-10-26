"""Breaking a message into the questions it contains."""

from __future__ import annotations

import re

# A fragment this short or shorter is not a question. One character cannot
# be one, and splitting on a full stop makes them: "e.g." becomes "e" and
# "g", which would otherwise be reported back as two questions nobody asked.
#
# Measured in characters rather than words on purpose — "remote?" is one
# word and a perfectly good question, which an earlier word-based rule
# folded into its neighbour and turned "remote? rates?" into "remote rates".
_SHORTEST_QUESTION = 1


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
    # `?` `;` and a newline end a question. `!` and `.` end a *sentence*,
    # which is how a greeting arrives attached to one: "Hi! Quick one — YOE
    # and CTC?" quoted the whole thing back as unanswered because none of it
    # was a separator. An em or en dash is used the same way in a hurried
    # message.
    #
    # A full stop is included despite the risk to "e.g." and "Mr." — a
    # question with either is rare, and a message with a full stop in the
    # middle is almost always two sentences.
    _TERMINATORS = re.compile(r"[?;!.\n]+|\s+[\u2014\u2013]\s+")
    # A comma, and a bare conjunction with no interrogative after it. Both
    # belong to the loose reading only: "whats your design rate, notice
    # period, and are you remote" is three questions in a list, while "Hello,
    # what are your rates" is one question with a greeting in front of it.
    # Nothing syntactic separates those, so the loose split is tried as a
    # second opinion and kept only when it finds strictly more answers.
    _BARE_CONJUNCTIONS = re.compile(
        r",\s*(?:and\s+|also\s+|plus\s+)?|\s+(?:and|also|plus|then)\s+",
        re.IGNORECASE,
    )
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
    def split_loosely(cls, message: str) -> list[str]:
        """Split on a bare conjunction too, without the interrogative test.

        The strict rule keeps "remote and hybrid work" whole, which is right,
        and keeps "comp and notice period" whole, which is not — neither half
        starts with an interrogative word and both are separate topics. No
        syntactic rule separates those two cases; the difference is meaning.

        So this exists as a *second opinion* rather than a replacement.
        `Index.answers` tries the strict split first and falls back to this
        only when the loose one answers strictly more questions, which is
        evidence that the parts were separate after all. A loose split that
        finds no extra answer is discarded, so the conservative behaviour is
        what survives by default.
        """
        parts: list[str] = []
        for sentence in cls._TERMINATORS.split(message):
            parts.extend(cls._BARE_CONJUNCTIONS.split(sentence))
        return cls._keep_usable(parts)

    @classmethod
    def looks_compound(cls, message: str) -> bool:
        """Whether this message might ask more than one thing.

        True when *either* split finds more than one part. It used to consult
        only the strict split, which reads "yoe and tech stack?" as one
        question — the loose split is the one that separates on "and", and
        that message is exactly the kind this is asked about.

        Deliberately generous, because its job is to decide whether the
        expensive reading is worth running: a false positive costs a scoring
        pass, and a false negative means a compound message is answered as
        though it asked one thing.
        """
        return len(cls.split(message)) > 1 or len(cls.split_loosely(message)) > 1

    #: Words that acknowledge rather than ask. Splitting "great, thanks!"
    #: yields "great" and "thanks"; the second is answerable and the first is
    #: not a question at all, so reporting it as unanswered made a correct
    #: reply look like a partial failure. Replace the set to change what
    #: counts as an acknowledgement.
    ACKNOWLEDGEMENTS: frozenset[str] = frozenset(
        {
            "great",
            "good",
            "ok",
            "okay",
            "cool",
            "nice",
            "right",
            "sure",
            "perfect",
            "lovely",
            "excellent",
            "awesome",
            "brilliant",
            "fine",
            "alright",
            "noted",
            "understood",
            "got it",
            "makes sense",
            "fair enough",
            "no worries",
        }
    )

    @classmethod
    def _keep_usable(cls, parts: list[str]) -> list[str]:
        """Drop the fragments that are not questions.

        A single word is kept: "remote?" is a question and the terminator
        already said so. An earlier version folded any single word into its
        neighbour and turned "remote? rates? notice period?" into two
        questions, the first of them "remote rates", which means neither.

        A single *character* is dropped, because splitting on a full stop
        makes them out of "e.g." and "U.S.".

        A bare acknowledgement is dropped too. "great, thanks!" splits into
        "great" and "thanks", and only the second is a thing to answer —
        reporting "great" as unanswered turned a correct reply into a
        partial failure in the measured runs.
        """
        kept = []
        for part in parts:
            cleaned = part.strip()
            if len(cleaned) <= _SHORTEST_QUESTION:
                continue
            if cleaned.strip(",.!? ").lower() in cls.ACKNOWLEDGEMENTS:
                continue
            kept.append(cleaned)
        return kept
