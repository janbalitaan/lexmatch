# Getting started

```python
from lexmatch import Entry, Index

index = Index([
    Entry(
        question="What is your notice period?",
        answer="One month.",
        aliases=["when can you start", "availability", "how soon"],
    ),
    Entry(
        question="Are you open to remote work?",
        answer="Yes, and I have done it for six years.",
        aliases=["remote", "work from home", "distributed team"],
    ),
])

entry, score = index.answer("how soon could you start?")
if entry:
    print(entry.answer)        # One month.
else:
    print("I don't have an answer for that.")
```

`answer()` returns a pair, and the first element is `None` when nothing
scored well enough. That shape is deliberate: a question-answering surface
that always returns *something* will eventually return the wrong thing
confidently, which is worse than admitting the gap.

## Installing

```bash
pip install lexmatch
```

No dependencies. It runs in a serverless function, in CI, or on a Raspberry
Pi, with nothing to install beyond the standard library.

## Seeing the scores

`score()` returns every entry, ranked, so you can see why a query matched:

```python
for value, entry in index.score("remote working")[:3]:
    print(f"{value:.3f}  {entry.question}")
```

```
0.667  Are you open to remote work?
0.000  What is your notice period?
```

Useful while writing aliases: a question that should match and scores near
zero usually needs a phrasing added, not a threshold lowered.

## Offering alternatives

When nothing matches, `suggestions()` gives the questions the index does
cover:

```python
entry, score = index.answer("what is your favourite colour?")
if entry is None:
    print("Try one of these:")
    for question in index.suggestions(limit=3):
        print(f"  {question}")
```

`suggestions()` returns at most `limit`, and fewer when the index is smaller
than that — so a two-entry index gives two, not two plus padding.
