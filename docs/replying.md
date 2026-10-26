# Replying like a chatbot

`answer()` returns a pair, which is enough to know whether anything matched.
It is not enough to behave like a chatbot, because a query can fail in three
different ways and each needs a different thing said.

```python
reply = index.reply(question)

if reply.answered:
    return reply.text

if reply.outcome is Outcome.AMBIGUOUS:
    # Strip the entries' own question marks, or the sentence ends in "??".
    options = " or ".join(e.question.rstrip("?") for e in reply.alternatives)
    return f"Which did you mean — {options}?"

if reply.outcome is Outcome.NEGATED:
    return "I want to be careful with that one. Could you rephrase it?"

return f"I don't have an answer for that. Try: {', '.join(reply.suggestions)}"
```

## Why a pair is not enough

The three failures look identical through `answer()` and are not:

| | `answer()` said | what should be said |
| --- | --- | --- |
| nothing matched | `(None, 0.0)` | "I don't know that. Try one of these." |
| two tied | **the first of them** | "Which did you mean — design or review?" |
| a negative question | **the affirmative answer** | nothing confident |

The middle row is the one that matters most, and it did not even return
`None`. Two entries tied at **0.727** and `answer()` picked the first — a
confident wrong answer half the time, with no way for the visitor to tell
which half they got.

```
'what is your rate'
  0.727  What is your rate for design work?
  0.727  What is your rate for review work?
```

The bottom row is worse in a different way. "Are you **not** open to remote
work" matches the affirmative entry at **0.923** and was answered "Yes" —
the opposite of correct. Lexical matching cannot tell a question from its
negation: they share every substantive word, and the negating words are
stopwords, stripped before scoring sees them.

## The four outcomes

```python
Outcome.ANSWERED      # one entry won clearly
Outcome.AMBIGUOUS     # two or more within the margin; offer them
Outcome.NEGATED       # the query was negative and the match is not
Outcome.UNANSWERED    # nothing cleared the threshold
```

`reply.text` is the answer when answered and `""` otherwise, so
`reply.text or fallback()` behaves.

## Suggestions are relevance-ranked

A query that nearly matched is offered what it nearly matched, not the first
few entries in the index:

```
'tools'   unanswered   ->  Which design tools do you use?
'work'    unanswered   ->  Are you open to remote work?
                          What is your rate for design work?
                          What is your rate for review work?
```

An entry scoring zero is not a near miss and is not offered. A query with no
overlap at all has no near miss, and falls back to the index's own order —
an honest menu rather than a pretend one.

## The ambiguity margin

```python
Index(entries, tuning=Tuning(ambiguity_margin=0.05))   # the default
```

How close the runner-up has to be before the question counts as ambiguous.
Only entries that **cleared the threshold** can be contenders — an entry
scoring zero is not a candidate however wide the margin.

Raise it to ask for clarification more often, lower it toward 0 to only
catch an exact tie. Zero still catches the 0.727 tie above, because that is
exact.

## Logging a turn

```python
log.info("lexmatch: %s", reply.describe())
# lexmatch: ambiguous, score 0.727, 2 alternatives, 2 suggestions
```

`describe()` carries the outcome and the shape of the result and **no
question or answer text**. A log of what visitors asked is personal data,
and its retention should be a deliberate decision rather than a side effect
of debugging.

## Negation is detected, not resolved

Knowing a question is negative does not say what the answer is. "Are you not
available" might be answered "no, I am available", and getting that right
needs the meaning of the entry rather than its words.

So the reply is marked, the closest match is still reported in
`alternatives`, and the caller decides — rephrase, escalate to a model, or
answer carefully. What it will not do is answer confidently wrong.

Two negatives agree: "aren't you remote" against "aren't you in the office"
are both negative, and that is not a mismatch. It is the disagreement that
inverts the answer.
