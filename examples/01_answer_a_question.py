"""The whole library in one screen.

An index of questions, a query, and an answer — or an honest refusal.

    python examples/01_answer_a_question.py
"""

from lexmatch import Entry, Index

index = Index(
    [
        Entry(
            question="Are you open to remote work?",
            answer="Yes, and I have done it for six years.",
            aliases=["remote", "work from home", "wfh", "distributed team"],
        ),
        Entry(
            question="What is your notice period?",
            answer="One month.",
            aliases=["when can you start", "availability", "how soon"],
        ),
        Entry(
            question="What are your rates?",
            answer="It depends on the scope. Happy to talk it through.",
            aliases=["pricing", "how much do you charge", "day rate"],
        ),
    ]
)

questions = [
    "how soon could you start?",
    "wfh?",
    "what do you charge",
    "what is your favourite film?",
]

for question in questions:
    entry, score = index.answer(question)
    print(f"Q: {question}")
    if entry:
        print(f"A: {entry.answer}   ({score:.3f})")
    else:
        # The point of the library: say so rather than answer something else.
        print(f"A: I don't have an answer for that.   ({score:.3f})")
        print(f"   Try: {', '.join(index.suggestions(limit=2))}")
    print()


print("--- or let it write the whole reply ---")
print()
for message in (
    "whats your rate, notice period, and are you remote?",
    "remote? and what is your favourite film?",
):
    print(f"> {message}")
    print(f"  {index.respond(message)}")
    print()
