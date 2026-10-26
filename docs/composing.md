# Composing a reply

```python
index.respond("whats your design rate, notice period, and are you remote?")
```

```
Design is £600 a day. I need one month's notice. And yes, I have worked
remotely for six years.
```

One call. `answers()` and `unanswered()` are still there for the structure
behind it, but assembling the sentence was the same code in every
application — and written badly, because the cases are not obvious until you
have hit them:

* three answers run together with no connective read as a dump;
* a missed question left unmentioned reads as having been understood;
* an ambiguous question answered at all reads as a guess.

## Every outcome gets the right sentence

```
'design rate?'
  Design is £600 a day.

'what is your rate'
  Which did you mean — What is your rate for design work or
  What is your rate for review work?

'are you not open to remote work'
  I want to be careful with that one — could you rephrase it?

'what is the weather'
  I don't have an answer for that. You could try: What is your rate for
  design work, What is your notice period

'design rate and what is your favourite film?'
  Design is £600 a day. I don't have an answer about your favourite film,
  though.
```

The last one is why a missed question is turned back into a *topic*. Quoted
whole it reads as a transcript of the input — "I don't have an answer about
**what is** your favourite film" — rather than as part of a reply.

## Nothing is invented

Every sentence in a response is either an entry's own answer or one of
`Composer`'s fixed phrases. There is no generation here, so a response can
say nothing the owner did not write. That is the point of using this instead
of a model for the common path.

An answer's wording is otherwise untouched. The only change is a full stop
when it has no closing punctuation, because several answers run together
without one read as a single long sentence meaning something else.

## A voice of your own

```python
class Warmer(Composer):
    NOTHING = "Hmm, that one's new to me."
    MISSED_ONE = "I'm afraid I don't know about {questions}!"
    AND = "Also, "

index = Index(entries, composer=Warmer)
```

```
Design is £600 a day. Also, yes, remotely for six years. I'm afraid I don't
know about your favourite film!
```

Every phrase is a class attribute, so you override the ones that matter and
keep the sequencing — the connective before the last of several, the
lower-casing after it, the comma-and-"and" of a list.

| | |
| --- | --- |
| `NOTHING` | nothing matched |
| `TRY_INSTEAD` | appended when there are questions worth offering |
| `WHICH` | the question was not specific enough |
| `NEGATIVE` | the question was asked in the negative |
| `MISSED_ONE` / `MISSED_SEVERAL` | part of a compound message found nothing |
| `AND` | joins the last of several answers |
| `OPENERS` | interrogative openings stripped from a quoted question |

## When to use what

| | |
| --- | --- |
| a chat box | `respond()` |
| your own wording, or a UI with buttons | `reply()` and `answers()` |
| routing to a model on a refusal | `reply()`, and check `reply.outcome` |

`respond()` is the top of the library. Underneath it, `answers()` splits the
message and replies to each part through `reply()` — so ambiguity and
negation are caught per question, not just for the message as a whole.
