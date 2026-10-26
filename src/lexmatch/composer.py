"""Turning what was found into something a person would say."""

from __future__ import annotations

from collections.abc import Sequence

from lexmatch.models.entry import Entry
from lexmatch.models.outcome import Outcome
from lexmatch.models.reply import Reply

# Two parts join with "and" and no comma; three or more take commas and a
# final "and". Named so the comparison says which case it is.
_PAIR = 2


class Composer:
    """Writes one reply out of several answers, or out of none.

    `answers()` returns a list and `unanswered()` returns the questions it
    missed, which leaves the caller writing the same joining logic every
    time — and writing it badly, because the cases are not obvious until you
    have hit them. Three answers run together with no connective read as a
    dump; a missed question left unmentioned reads as having been understood;
    an ambiguous question answered at all reads as a guess.

    The wording is deliberately plain and replaceable. Every phrase is a
    class attribute, so an application with a voice of its own overrides what
    it needs and keeps the sequencing:

        class Warmer(Composer):
            NOTHING = "Hmm, I'm not sure about that one."
            MISSED_ONE = "I don't know about {questions}, sorry!"

    Nothing here invents content. Every sentence is either an entry's own
    answer or one of these fixed phrases, so a composed reply can say nothing
    the owner did not write.
    """

    #: Said when nothing matched at all.
    NOTHING = "I don't have an answer for that."
    #: Appended to `NOTHING` when there are questions worth offering.
    TRY_INSTEAD = "You could try: {questions}"
    #: Said when the question was understood but was not specific enough.
    WHICH = "Which did you mean — {options}?"
    #: Said when the question was asked in the negative.
    NEGATIVE = "I want to be careful with that one — could you rephrase it?"
    #: Appended when some of a compound message went unanswered.
    MISSED_ONE = "I don't have an answer about {questions}, though."
    MISSED_SEVERAL = "I don't have answers about {questions}, though."
    #: Joins the final answer of several.
    AND = "And "

    @classmethod
    def compose(
        cls,
        answers: Sequence[tuple[Entry, float]],
        missed: Sequence[str] = (),
    ) -> str:
        """Write one reply covering every answer, and what was missed.

        The order of `answers` is the order asked, which is the order a
        person expects them back in.
        """
        if not answers:
            return cls._nothing(missed)
        sentences = [cls._sentence(entry.answer) for entry, _ in answers]
        if len(sentences) > 1:
            # A connective before the last one, so three answers read as a
            # list rather than as three separate statements that happen to
            # be adjacent.
            sentences[-1] = cls.AND + cls._lower_first(sentences[-1])
        if missed:
            sentences.append(cls._missed(missed))
        return " ".join(sentences)

    @classmethod
    def compose_reply(cls, reply: Reply) -> str:
        """Write one reply from a single `Reply`, whatever its outcome."""
        if reply.outcome is Outcome.ANSWERED and reply.entry:
            return cls._sentence(reply.entry.answer)
        if reply.outcome is Outcome.AMBIGUOUS:
            return cls.WHICH.format(options=cls._options(reply.alternatives))
        if reply.outcome is Outcome.NEGATED:
            return cls.NEGATIVE
        return cls._nothing(reply.suggestions)

    @classmethod
    def _nothing(cls, suggestions: Sequence[str]) -> str:
        """Say there is no answer, and offer what there is."""
        if not suggestions:
            return cls.NOTHING
        offered = ", ".join(question.strip().rstrip("?") for question in suggestions)
        return f"{cls.NOTHING} {cls.TRY_INSTEAD.format(questions=offered)}"

    #: Interrogative openings stripped when a missed question is quoted
    #: back. "I don't have an answer about *what is* your favourite film"
    #: reads as a transcript; "about your favourite film" reads as a reply.
    OPENERS = (
        "what is",
        "what are",
        "what do",
        "whats",
        "when is",
        "when can",
        "where is",
        "who is",
        "how is",
        "how do",
        "how much",
        "why is",
        "do you know",
        "do you have",
        "do you",
        "does your",
        "did you",
        "are you",
        "is your",
        "can you",
        "could you",
        "will you",
        "would you",
        "tell me about",
    )

    @classmethod
    def _missed(cls, missed: Sequence[str]) -> str:
        """Name the parts of a message that found nothing.

        Said rather than left out. Answering two of three questions and
        saying nothing about the third reads as having understood it.
        """
        questions = cls._join([cls._as_topic(question) for question in missed])
        template = cls.MISSED_ONE if len(missed) == 1 else cls.MISSED_SEVERAL
        return template.format(questions=questions)

    @classmethod
    def _options(cls, entries: Sequence[Entry]) -> str:
        """List the contenders for a clarifying question."""
        return " or ".join(entry.question.rstrip("?") for entry in entries)

    @classmethod
    def _as_topic(cls, question: str) -> str:
        """Turn a question back into the thing it was about.

        Quoted whole, a missed question reads as a transcript of the input
        rather than as part of a reply. Stripping the interrogative opening
        is enough to make it read as a topic, and anything it does not
        recognize is quoted as it came — a slightly stiff sentence being
        better than a mangled one.
        """
        trimmed = question.strip().rstrip("?").strip()
        lowered = trimmed.lower()
        for opener in cls.OPENERS:
            if lowered.startswith(f"{opener} "):
                return trimmed[len(opener) + 1 :]
        return trimmed

    @staticmethod
    def _join(parts: Sequence[str]) -> str:
        """Join with commas and a final "and", as somebody would say it."""
        if len(parts) == 1:
            return parts[0]
        if len(parts) == _PAIR:
            return f"{parts[0]} and {parts[1]}"
        return f"{', '.join(parts[:-1])} and {parts[-1]}"

    @staticmethod
    def _sentence(text: str) -> str:
        """Give the text a full stop if it has no closing punctuation.

        An owner's answer is their wording and is not otherwise touched —
        but run together without punctuation, several answers read as one
        long sentence that means something else.
        """
        stripped = text.strip()
        if not stripped or stripped[-1] in ".!?…":
            return stripped
        return f"{stripped}."

    @staticmethod
    def _lower_first(text: str) -> str:
        """Lower-case the first letter after a connective.

        "And Yes, I have" reads wrong. Only the first character, and only
        when the second is lower-case — so an initialism or a name keeps its
        capital: "And NDAs are fine" stays as it is.
        """
        if len(text) > 1 and text[1].islower():
            return text[0].lower() + text[1:]
        return text
