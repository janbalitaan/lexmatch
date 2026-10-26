"""Seeing the scores, which is how you write good aliases.

`score()` ranks every entry, so a question that should match and does not
shows you what to add.

    python examples/02_why_did_it_match.py
"""

from lexmatch import Entry, Index

index = Index(
    [
        Entry(question="Are you open to remote work?", answer="Yes.", aliases=["remote"]),
        Entry(question="What is your notice period?", answer="One month."),
        Entry(question="What are your rates?", answer="It depends on scope."),
    ]
)

for query in ("remote", "day rate", "when could you start"):
    print(f"{query!r}")
    for value, entry in index.score(query)[:3]:
        marker = "  <-- answered" if value >= index.threshold else ""
        print(f"  {value:.3f}  {entry.question}{marker}")
    print()

print("'day rate' and 'when could you start' score zero: they share no")
print("substantive word with any question. No threshold reaches that — the")
print("fix is an alias, not a smaller number.")
