# Questions that ask more than one thing

```python
for entry, score in index.answers("are you remote and what are your rates?"):
    print(entry.answer)
```

## Why `answer()` is not enough

A message asking two things scores **worse** against both than either would
alone. The reason is arithmetic rather than a defect: the phrase measure is
an overlap ratio, so doubling the query's length halves the proportion any
single entry can share.

Measured on a three-part message:

```
'remote? rates? notice period?'

answer()                    0.480   one reply, two questions silently dropped
  0.480  What is your notice period?
  0.400  Are you open to remote work?     ← below the threshold
  0.250  What are your rates?             ← below the threshold
```

Two of the three fell under the threshold, so asking three things got *one*
answer and no indication that anything was missed.

## What `answers()` does

Splits first, then answers each question on its own:

```
answers()
  1.000  Yes, six years of it.
  0.980  It depends on scope.
  0.959  One month.
```

Each question scores as if it had been asked alone, because it was.

Returns one pair per question that found an answer, in the order asked. A
message with two questions and one answerable returns a list of one — and
an empty list means nothing was answerable, which is what `answer()` reports
as `None`.

**Duplicates are collapsed.** "rates? pricing?" are two questions with one
answer, and giving it twice reads as a malfunction.

## Saying what you missed

```python
replies = index.answers(message)
missed = index.unanswered(message)

for entry, _ in replies:
    print(entry.answer)
if missed:
    print(f"I don't have an answer for: {'; '.join(missed)}")
```

A message asking three things where two are covered should say so. Replying
to two and leaving the third unmentioned reads as having understood it.

```
'what are your rates and what is your favourite film?'
  answers():    1.000  It depends on scope.
  unanswered(): ['what is your favourite film']
```

## What counts as a split

Conservative, because a wrong split answers a question nobody asked.

**Always split:** `?`, `;`, a newline.

**Split on `and`, `also`, `plus`, `then` only before an interrogative word** —
what, when, where, who, why, how, which, do, does, did, are, is, was, can,
could, will, would, should, have, has, had.

That distinction is what keeps one question whole:

```
'are you open to remote and hybrid work?'   ->  one question
'what is your rate and availability'        ->  one question
'what are your rates and when can you start?'  ->  two
```

A word before a question mark is a question — `remote? rates?` is two, not
one. An earlier version folded single words into their neighbour and turned
that into `['remote rates', ...]`, which means neither.

## When to use which

`answer()` treats the whole message as one question, which is right when you
control the input or expect one question at a time. `answers()` is for a chat
box, where somebody types everything they want to know in one go.

`QuestionSplitter.looks_compound(message)` tells you which you are holding,
if you would rather decide yourself.
