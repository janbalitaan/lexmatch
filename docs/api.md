# API reference

Everything importable from `lexmatch`. Nothing else is public.

```python
from lexmatch import (
    # matching
    Entry, Index, QuestionSplitter, SmallTalk,
    # tuning
    Tuning, Synonyms, Corrections,
    # text
    normalize, query_terms,
    # errors
    LexmatchError, SmallTalkError, SynonymError, TuningError,
    # constants
    DEFAULT_THRESHOLD, LENGTH_PENALTY, MIN_CONTENT_OVERLAP,
    TERM_FREQUENCY_SATURATION, STOPWORDS, __version__,
)
```

## `Entry`

```python
Entry(question, answer, aliases=[], tags=[])
```

| | |
| --- | --- |
| `question` | how the question is canonically asked |
| `answer` | what to reply. Returned verbatim |
| `aliases` | other phrasings. See [aliases](aliases.md) |
| `tags` | yours to use; scoring ignores them |

## `Index`

```python
Index(entries, threshold=None, tuning=None)
```

`threshold` wins over `tuning.threshold` when both are given: a caller who
named it explicitly meant it.

| Method | Returns | |
| --- | --- | --- |
| `.answer(query)` | `(Entry \| None, float)` | the best entry if it clears the threshold |
| `.answers(message)` | `list[tuple[Entry, float]]` | one answer per question in a compound message |
| `.unanswered(message)` | `list[str]` | the questions in it that found nothing |
| `.score(query)` | `list[tuple[float, Entry]]` | every entry, ranked, best first |
| `.suggestions(limit=5)` | `list[str]` | questions the index covers |
| `.tuning` | `Tuning` | what is in force |
| `.threshold` | `float` | the threshold, for convenience |

`answer()` returning `None` is the point of the library — see
[refusing](refusing.md).

## `Tuning`

```python
Tuning(threshold=0.45, saturation=1.4, length_penalty=0.72,
       minimum_overlap=1, stopwords=STOPWORDS, synonyms=Synonyms())
```

Frozen; every adjustment returns a new one.

| Method | |
| --- | --- |
| `.with_threshold(value)` | answer more or less readily |
| `.with_stopwords(words, *, extra, keep)` | replace, add to, or subtract from the list |
| `.with_synonyms(pairs)` | read words as each other, index-wide |
| `.with_corrections(*, enabled, similarity, minimum_length)` | read mistyped words as real ones |
| `.describe()` | safe to log |

See [tuning](tuning.md) for what each number does and when to move it.

## Text

```python
normalize(text, keep_stopwords=False) -> list[str]
query_terms(text) -> list[str]
```

`normalize` case-folds, drops punctuation and removes stopwords.
`query_terms` is what the scorer calls on a query. Both are exported because
an application that wants to match the library's tokenization — for
highlighting, say — should not have to guess at it.

## `Synonyms`

```python
Synonyms.of({"wfh": "work from home", "comp": "compensation"})
```

| Method | |
| --- | --- |
| `.expand(tokens)` | the tokens with known synonyms expanded in place |
| `.with_pairs(pairs)` | these synonyms plus more |
| `.describe()` | safe to log |

Declared once for the whole index, where an alias would be per entry. Both
the entries and the queries go through the same map. See
[synonyms](synonyms.md).

## `Corrections`

```python
Corrections(similarity=0.8, minimum_length=4, enabled=True)
```

Reads a mistyped word as the index's own word. `'whats your raets'` scored
0.000 before and is answered now. Only tokens **not** already in the
vocabulary are touched, and only when exactly one candidate is close enough
— a tie means the word is ambiguous. See [typos](typos.md).

## `SmallTalk`

```python
SmallTalk.entries({"greeting": "Hello.", "thanks": "You're welcome."})
SmallTalk.phrasings_for("greeting")
SmallTalk.INTENTS
```

Builds entries for greetings, farewells, thanks, identity, capability and
wellbeing. The phrasings are shipped — how somebody says hello is the same
everywhere — and the replies are yours. See [small talk](small-talk.md).

## `QuestionSplitter`

```python
QuestionSplitter.split(message) -> list[str]
QuestionSplitter.split_loosely(message) -> list[str]
QuestionSplitter.looks_compound(message) -> bool
```

Separates a message that asks more than one thing. `Index.answers()` uses
it; it is exported so an application can decide for itself whether to treat
a message as one question or several.

## Errors

```python
LexmatchError          # the base; catch this to catch everything
SynonymError           # a synonym that could never match. Also a ValueError
TuningError            # a tuning value outside its range. Also a ValueError
```

## Constants

```python
DEFAULT_THRESHOLD           # 0.45
TERM_FREQUENCY_SATURATION   # 1.4,  BM25's k1
LENGTH_PENALTY              # 0.72, BM25's b
MIN_CONTENT_OVERLAP         # 1
STOPWORDS                   # frozenset, 77 words
__version__
```

Exported so a caller can build on a default rather than copy its value:
`Tuning(threshold=DEFAULT_THRESHOLD + 0.1)`, or
`Tuning().with_stopwords(STOPWORDS | {"please"})`.
