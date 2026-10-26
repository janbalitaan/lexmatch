# API reference

Everything importable from `lexmatch`. Nothing else is public.

```python
from lexmatch import (
    # matching
    Entry, Index, Reply, Outcome, Composer,
    QuestionSplitter, SmallTalk, Negation,
    # reading a question set from a file
    JsonParser, CsvParser, MarkdownParser,
    # tuning
    Tuning, Synonyms, Corrections,
    # how words are read
    Stemmer, Morphology, Contractions,
    # text
    normalize, query_terms,
    # errors
    LexmatchError, EntryError, ParseError,
    SmallTalkError, SynonymError, TuningError,
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
| `.respond(message)` | `str` | the whole turn, written as a sentence |
| `.reply(query)` | `Reply` | the answer, or which of three ways it failed |
| `.answer(query)` | `(Entry \| None, float)` | the best entry if it clears the threshold |
| `.answers(message)` | `list[tuple[Entry, float]]` | one answer per question in a compound message |
| `.unanswered(message)` | `list[str]` | the questions in it that found nothing |
| `.score(query)` | `list[tuple[float, Entry]]` | every entry, ranked, best first |
| `.suggestions(limit=5)` | `list[str]` | questions the index covers |
| `.tuning` | `Tuning` | what is in force |
| `.threshold` | `float` | the threshold, for convenience |

`answer()` returning `None` is the point of the library — see
[refusing](refusing.md).

## `Composer`

```python
Composer.compose(answers, missed) -> str
Composer.compose_reply(reply) -> str
```

Writes one reply out of several answers, or out of none. `Index.respond()`
uses it; subclass it for a voice of your own:

```python
class Warmer(Composer):
    NOTHING = "Hmm, that one's new to me."
    MISSED_ONE = "I'm afraid I don't know about {questions}!"
    AND = "Also, "

Index(entries, composer=Warmer)
```

Every phrase is a class attribute, so an override keeps the sequencing.
Nothing is invented: every sentence is either an entry's own answer or one of
these phrases. See [composing](composing.md).

## `Reply`

```python
reply = index.reply("what is your rate")

reply.outcome        # Outcome.ANSWERED | AMBIGUOUS | NEGATED | UNANSWERED
reply.answered       # bool
reply.text           # the answer, or "" when there is none
reply.entry          # Entry | None
reply.score          # float
reply.alternatives   # tuple[Entry, ...] — the close contenders
reply.suggestions    # tuple[str, ...] — what to offer instead
reply.describe()     # safe to log; carries no question or answer text
```

`answer()` is enough to know whether anything matched. `reply()` is enough to
behave like a chatbot, because the three ways a query fails each need a
different thing said. See [replying](replying.md).

## `Outcome`

```python
Outcome.ANSWERED      # one entry won clearly
Outcome.AMBIGUOUS     # two or more tied; offer the alternatives
Outcome.NEGATED       # the query was negative and the match is not
Outcome.UNANSWERED    # nothing cleared the threshold
```

A `str` enum, so it serializes as its name.

## `Negation`

```python
Negation.present_in(text) -> bool
Negation.disagree(query, question) -> bool
```

Detection, not resolution. Knowing a question is negative does not say what
the answer is — "are you not available" might be answered "no, I am
available" — so the reply is marked and the caller decides.

## `Tuning`

```python
Tuning(threshold=0.45, saturation=1.4, length_penalty=0.72,
       minimum_overlap=1, ambiguity_margin=0.05,
       stopwords=STOPWORDS, synonyms=Synonyms(), corrections=Corrections())
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

## Reading a question set from a file

```python
JsonParser.read(path) -> list[Entry]
JsonParser.parse(text) -> list[Entry]
CsvParser.read(path) -> list[Entry]
CsvParser.parse(text) -> list[Entry]
MarkdownParser.read(path) -> list[Entry]
MarkdownParser.parse(text) -> list[Entry]
```

A question set is content, and content belongs to whoever writes the answers.
Each parser raises `ParseError` naming the line, row or key at fault.

```python
index = Index(CsvParser.read("faq.csv"))
```

`JsonParser` accepts a bare list or an object wrapping one under `entries`,
`questions`, `faq`, `items` or `data`, and ignores keys an `Entry` does not
have. `CsvParser` matches column names case-insensitively, accepts `q`/`a`
and `prompt`/`response`, and splits several aliases in one cell on a
semicolon. `MarkdownParser` reads a level-two heading as the question, the
prose under it as the answer, an italic *"Also asked: …"* line as aliases and
a line of `#hashtags` as tags. Each class exposes its field names and
separators as class attributes, so a file named differently loads without
being rewritten.

## `Stemmer`

```python
Stemmer.stem(word) -> str
Stemmer.stem_all(words) -> list[str]
Stemmer.forget() -> None            # after changing the tables in place
Stemmer.IRREGULAR, Stemmer.KEEP, Stemmer.SUFFIXES
```

Folds inflection onto one token — plurals, tenses, adverbs — and deliberately
not derivation. See `stemming.md`. Replace it wholesale with
`Tuning().with_stemmer(...)`, or `None` to match exact word forms.

## `Morphology`

```python
Morphology.extend(token, vocabulary) -> str
Morphology.extend_all(tokens, vocabulary) -> list[str]
Morphology.SHORTEST_PREFIX, Morphology.STOP_AT
```

Reads a query word as the longer index word built from it, by prefix:
"senior" to "seniority". Only lengthens toward a word the index holds, and
refuses an ambiguous prefix. Replace with `Tuning().with_morphology(...)`.

## `Contractions`

```python
Contractions.expand(words) -> list[str]
Contractions.holds(word) -> bool
Contractions.FORMS
```

Replaces a contraction with the words it stands for, keyed on the
apostrophe-stripped form. See `informal-writing.md`.

## Errors

```python
LexmatchError          # the base; catch this to catch everything
EntryError             # an entry with no question or no answer
ParseError             # a question set file that could not be read
SmallTalkError         # a small-talk intent that does not exist
SynonymError           # a synonym that could never match. Also a ValueError
TuningError            # a tuning value outside its range. Also a ValueError
```

## Constants

```python
DEFAULT_THRESHOLD           # 0.45
TERM_FREQUENCY_SATURATION   # 1.4,  BM25's k1
LENGTH_PENALTY              # 0.72, BM25's b
MIN_CONTENT_OVERLAP         # 1
STOPWORDS                   # frozenset, 137 words
__version__
```

Exported so a caller can build on a default rather than copy its value:
`Tuning(threshold=DEFAULT_THRESHOLD + 0.1)`, or
`Tuning().with_stopwords(STOPWORDS | {"please"})`.
