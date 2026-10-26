# API reference

Everything importable from `lexmatch`. Nothing else is public.

```python
from lexmatch import (
    # matching
    Entry, Index,
    # tuning
    Tuning,
    # text
    normalize, query_terms,
    # errors
    LexmatchError, TuningError,
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
| `.score(query)` | `list[tuple[float, Entry]]` | every entry, ranked, best first |
| `.suggestions(limit=5)` | `list[str]` | questions the index covers |
| `.tuning` | `Tuning` | what is in force |
| `.threshold` | `float` | the threshold, for convenience |

`answer()` returning `None` is the point of the library — see
[refusing](refusing.md).

## `Tuning`

```python
Tuning(threshold=0.45, saturation=1.4, length_penalty=0.72,
       minimum_overlap=1, stopwords=STOPWORDS)
```

Frozen; every adjustment returns a new one.

| Method | |
| --- | --- |
| `.with_threshold(value)` | answer more or less readily |
| `.with_stopwords(words, *, extra, keep)` | replace, add to, or subtract from the list |
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

## Errors

```python
LexmatchError          # the base; catch this to catch everything
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
