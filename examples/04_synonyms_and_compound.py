"""A word that means the same thing everywhere, and a message asking several.

Two problems aliases alone do not solve: a short form you use index-wide, and
a visitor who types everything they want to know in one go.

    python examples/04_synonyms_and_compound.py
"""

from lexmatch import Entry, Index, Tuning

entries = [
    Entry(
        question="Are you open to remote work?",
        answer="Yes, six years of it.",
        aliases=["remote", "work from home"],
    ),
    Entry(
        question="What is your compensation expectation?",
        answer="Negotiable, and I would rather talk about scope first.",
        aliases=["pay", "salary"],
    ),
    Entry(
        question="What is your notice period?",
        answer="One month.",
        aliases=["when can you start", "availability"],
    ),
]

print("a short form nobody wrote an alias for:")
plain = Index(entries)
for query in ("wfh", "comp"):
    entry, score = plain.answer(query)
    print(f"  {query!r:<8} {score:.3f}  {'answered' if entry else 'refused'}")

print()
print("one synonym map instead of an alias in every entry:")
index = Index(
    entries,
    tuning=Tuning().with_synonyms({"wfh": "work from home", "comp": "compensation"}),
)
for query in ("wfh", "comp"):
    entry, score = index.answer(query)
    print(f"  {query!r:<8} {score:.3f}  {entry.answer if entry else 'refused'}")

print()
print("a message asking three things, answered as one question:")
message = "wfh? comp? when can you start?"
entry, score = index.answer(message)
print(f"  answer()   {score:.3f}  {entry.answer if entry else 'refused'}")
print("  the other two scored below the threshold and were dropped silently")

print()
print("the same message, split first:")
for entry, score in index.answers(message):
    print(f"  answers()  {score:.3f}  {entry.answer}")

print()
print("and when part of it is not covered, say so:")
mixed = "what is your notice period and what is your favourite film?"
for entry, score in index.answers(mixed):
    print(f"  {score:.3f}  {entry.answer}")
for missed in index.unanswered(mixed):
    print(f"  no answer for: {missed!r}")


print()
print("--- and the three ways a question can fail ---")
from lexmatch import Outcome

ambiguous = Index(
    [
        Entry(question="What is your rate for design work?", answer="£600/day."),
        Entry(question="What is your rate for review work?", answer="£500/day."),
        Entry(question="Are you open to remote work?", answer="Yes."),
    ]
)

for question in (
    "design rate",
    "what is your rate",
    "are you not open to remote work",
    "what is the weather",
):
    reply = ambiguous.reply(question)
    print(f"  {question!r}")
    print(f"    {reply.describe()}")
    if reply.answered:
        print(f"    -> {reply.text}")
    elif reply.outcome is Outcome.AMBIGUOUS:
        options = " or ".join(entry.question.rstrip("?") for entry in reply.alternatives)
        print(f"    -> Which did you mean — {options}?")
    elif reply.outcome is Outcome.NEGATED:
        print("    -> asked in the negative; the closest match says the opposite")
    else:
        print(f"    -> I don't have that. Try: {', '.join(reply.suggestions[:2])}")
