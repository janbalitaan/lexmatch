"""The things people say that are not questions about anything."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from lexmatch.exceptions import SmallTalkError
from lexmatch.models.entry import Entry

# How people open, close and acknowledge, by intent. These are shipped
# because they are the same everywhere — "hiya" is "hiya" whatever the index
# is about — while the *replies* are not, so they come from the caller.
#
# A bot that refuses "thanks!" reads as broken in a way that a bot refusing
# an obscure question does not: the visitor knows they said something
# ordinary, so the failure looks like the bot rather than like the question.
PHRASINGS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "greeting": (
            "hello",
            "hi",
            "hiya",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
            "greetings",
            "yo",
            "howdy",
        ),
        "farewell": (
            "goodbye",
            "bye",
            "see you",
            "see ya",
            "later",
            "take care",
            "that is all",
            "that will be all",
            "nothing else",
        ),
        "thanks": (
            "thanks",
            "thank you",
            "thanks a lot",
            "much appreciated",
            "appreciate it",
            "cheers",
            "ta",
        ),
        "identity": (
            "who are you",
            "what are you",
            "are you a bot",
            "are you human",
            "are you a real person",
            "are you an ai",
            "what is this",
        ),
        "capability": (
            "what can you do",
            "what can i ask",
            "what do you know",
            "help",
            "how does this work",
            "what should i ask",
        ),
        "wellbeing": (
            "how are you",
            "how is it going",
            "how do you do",
            "you ok",
            "hows things",
        ),
    }
)


class SmallTalk:
    """Builds entries for the conversational turns, from your replies.

    The split is deliberate. How somebody says hello is the same whatever the
    index is about, so the phrasings are shipped. What the bot says back is
    not — it depends on whose bot it is — so the replies come from the caller
    and nothing is answered until they do.

        Index([
            *SmallTalk.entries({
                "greeting": "Hello. Ask me anything about Jan's work.",
                "thanks": "You're welcome.",
            }),
            *my_entries,
        ])

    An intent with no reply is simply not added, so a caller who only wants
    greetings handled gets greetings handled.
    """

    INTENTS = tuple(PHRASINGS)

    @staticmethod
    def entries(replies: Mapping[str, str]) -> list[Entry]:
        """Return an entry per intent the caller gave a reply for.

        An unknown intent raises rather than being ignored: the usual cause
        is a typo, and a silently absent greeting handler looks exactly like
        one that is working until somebody says hello.
        """
        unknown = sorted(set(replies) - set(PHRASINGS))
        if unknown:
            raise SmallTalkError(
                f"no such small-talk intent: {', '.join(unknown)}. "
                f"Available: {', '.join(SmallTalk.INTENTS)}"
            )
        built = []
        for intent, reply in replies.items():
            if not reply.strip():
                continue
            phrasings = PHRASINGS[intent]
            built.append(
                Entry(
                    # The first phrasing is the canonical one, the rest are
                    # aliases — which is exactly the shape an entry wants.
                    question=phrasings[0],
                    answer=reply,
                    aliases=list(phrasings[1:]),
                    tags=["smalltalk", intent],
                )
            )
        return built

    @staticmethod
    def phrasings_for(intent: str) -> tuple[str, ...]:
        """Return how people express this intent, for a caller extending it."""
        if intent not in PHRASINGS:
            raise SmallTalkError(
                f"no such small-talk intent: {intent}. "
                f"Available: {', '.join(SmallTalk.INTENTS)}"
            )
        return PHRASINGS[intent]
