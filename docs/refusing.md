# Refusing to answer

`answer()` returns `(None, score)` when nothing clears the threshold. That is
the most important thing this library does, and the reason it exists rather
than a one-line `max()` over difflib ratios.

```python
entry, score = index.answer(question)
if entry is None:
    return "I don't have an answer for that."
return entry.answer
```

## Why refusing matters more than matching

A question-answering surface that always returns *something* returns the
wrong thing, confidently, the first time it is asked something outside its
index. On a personal site that means a visitor reading an answer about your
notice period when they asked about your rates — and nothing in the reply
tells them it is unrelated.

A refusal costs a visitor one more click. A confident wrong answer costs them
the assumption that anything else on the page is right.

## What the scores actually look like

```
'remote'                      1.000   answered
'how soon can you start'      0.952   answered
'what is the capital of france'  0.000   refused
'do you enjoy cooking'        0.000   refused
''                            0.000   refused
```

Note the shape: a match is usually *well* above the 0.45 threshold and a
non-match is usually zero, not 0.3. Scores cluster at the ends because both
measures need a substantive word in common before they report anything at
all. The threshold is there for the narrow middle, not to split a continuum.

That clustering is also what the refusals depend on, and it has a cost at
the edge. *"do you like working alone"* scores **1.000** against *"Are you
open to remote work?"*, because "working" folds to "work" and "alone" is a
word this index has never seen — so the only content word left is one they
share. `limitations.md` has the two measured attempts at charging for an
unknown word, and why neither is the default.

## Choosing the threshold

The default is 0.45. Move it by watching real questions, not by reasoning
about the number:

**Raise it** when a wrong answer costs more than no answer, which is most of
the time. 0.6 is a reasonable second choice.

**Lower it** only after writing [aliases](aliases.md). A query that should
match and scores 0.2 needs a phrasing added; lowering the threshold to catch
it also catches everything else at 0.2, and those are the wrong answers.

**Above 1.0** refuses everything, since scores cap at 1.0. That is the honest
way to turn answering off — a maintenance mode, or a test that wants no match
without reaching for a mock.

```python
Index(entries, threshold=0.6)
Index(entries, tuning=Tuning().with_threshold(0.6))
```

## Offering something instead

```python
if entry is None:
    return "I don't have that. Try: " + ", ".join(index.suggestions(limit=3))
```

`suggestions()` returns the questions the index covers, up to `limit` and
fewer when the index is smaller. Turning a dead end into a menu is most of
what makes a refusal acceptable to the person reading it.
