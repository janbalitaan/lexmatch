"""A product support desk, which is what this costs nothing to run.

The question set is the whole of the configuration — no model, no API key,
no per-message cost, and an answer in well under a millisecond. The three
things a support index needs that a personal one does not are all here:

    refusing          a wrong answer about billing is worse than no answer
    learning          `unanswered` is the backlog of articles to write
    an escalation     what to say when it genuinely does not know

    python examples/05_a_support_desk.py
"""

from lexmatch import Entry, Index, Outcome, SmallTalk, Tuning

ESCALATION = "I don't have an article on that. support@example.com will know."

FAQ = [
    *SmallTalk.entries(
        {
            "greeting": "Hello. Ask me anything about your account or billing.",
            "thanks": "Happy to help.",
            "farewell": "Take care.",
            "identity": "I'm the support assistant for Example.",
            "capability": "I can help with billing, plans, refunds and account access.",
            "wellbeing": "All good here.",
        }
    ),
    Entry(
        question="How do I reset my password?",
        answer="Use the Forgot password link on the sign-in page.",
        aliases=["reset password", "forgot password", "locked out", "cannot sign in"],
        tags=["account"],
    ),
    Entry(
        question="How do I cancel my subscription?",
        answer="Settings, then Billing, then Cancel plan. It runs to the period end.",
        aliases=["cancel", "cancel plan", "unsubscribe", "stop billing", "end my plan"],
        tags=["billing"],
    ),
    Entry(
        question="What is your refund policy?",
        answer="Full refund within 14 days of a charge. Email support with the invoice.",
        aliases=["refund", "money back", "get a refund", "chargeback"],
        tags=["billing"],
    ),
    Entry(
        question="How do I change my payment card?",
        answer="Settings, then Billing, then Payment method.",
        aliases=["update card", "change card", "new card", "payment details"],
        tags=["billing"],
    ),
    Entry(
        question="Can I upgrade or downgrade my plan?",
        answer="Any time, from Settings then Billing. Changes are prorated.",
        aliases=["upgrade", "downgrade", "change plan", "switch plan"],
        tags=["plans"],
    ),
    Entry(
        question="Do you offer a free trial?",
        answer="Fourteen days on any plan, no card needed.",
        aliases=["free trial", "trial", "try it first"],
        tags=["plans"],
    ),
    Entry(
        question="Where can I find my invoices?",
        answer="Settings, then Billing, then Invoices. Each one downloads as a PDF.",
        aliases=["invoice", "invoices", "receipt", "billing history"],
        tags=["billing"],
    ),
    Entry(
        question="How do I add a teammate?",
        answer="Settings, then Team, then Invite. They get an email.",
        aliases=["add user", "invite someone", "add teammate", "seats"],
        tags=["account"],
    ),
]

# A support index is deliberately narrow, so most of what it is asked is out
# of scope. Raising the threshold and charging for words it does not know
# both trade recall for fewer wrong answers, which is the right trade when a
# wrong answer about billing costs a support ticket and some trust.
index = Index(FAQ, threshold=0.55, tuning=Tuning(unknown_word_cost=0.5))


def reply_to(message: str) -> str:
    """Answer, or escalate. Never guess.

    "cancel my plan and refund me" is two requests, and answering only the
    first is how a support bot generates the ticket it existed to prevent —
    so every answer the reading found is given.
    """
    reply = index.reply(message)
    if reply.outcome is Outcome.ANSWERED:
        answers = [reply.entry.answer, *(entry.answer for entry in reply.alternatives)]
        return " ".join(answers)
    if reply.outcome is Outcome.AMBIGUOUS:
        options = " or ".join(entry.question for entry in reply.alternatives)
        return f"Did you mean {options}?"
    return ESCALATION


CONVERSATION = [
    "hi",
    "i'm locked out of my account",
    "how do i cancel",
    "can i get my money back",
    "where are my receipts",
    "i want to add two colleagues",
    "do you integrate with Salesforce?",
    "what's the weather in Berlin",
    "cancel my plan and refund me",
    "thanks!",
]

print("A support conversation\n")
for message in CONVERSATION:
    answer = reply_to(message)
    escalated = " (escalated)" if answer == ESCALATION else ""
    print(f"  visitor:  {message}")
    print(f"  desk:     {answer}{escalated}\n")

# What the index could not answer is the backlog. In production this is
# logged and read weekly: every line is either an alias to add or an article
# to write, and nothing else tells you what your customers wanted.
print("What to write next, from what went unanswered\n")
missed = [question for message in CONVERSATION for question in index.unanswered(message)]
for question in missed:
    print(f"  {question!r}")
print(f"\n  {len(missed)} of {len(CONVERSATION)} messages had something unanswered.")
